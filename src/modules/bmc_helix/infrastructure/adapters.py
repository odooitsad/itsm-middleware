import asyncio
from collections.abc import AsyncGenerator

import httpx

from src.core.clients.http import HttpClient, HttpResponse
from src.core.exceptions import HttpClientError
from src.core.logger import get_logger
from src.modules.bmc_helix.domain.entities import (
    BmcHelixError,
    CreateIncidentInput,
    IncidentInfo,
    IncidentResponse,
)
from src.modules.bmc_helix.domain.exceptions import (
    BmcHelixClientError,
    IncidentCreationError,
)
from src.modules.bmc_helix.domain.ports import BmcHelixPort

logger = get_logger(__name__)


class BmcHelixAuth(httpx.Auth):
    """
    httpx.Auth implementation for BMC Helix JWT authentication.

    Fetches a JWT from /jwt/login using form-encoded credentials, caches it,
    and auto-refreshes transparently on 401 responses (one retry per request).
    """

    def __init__(self, base_url: str, username: str, password: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._username = username
        self._password = password
        self._token: str | None = None
        self._cookies: dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def _fetch_token(self) -> str:
        """POST to /jwt/login with form-encoded credentials and return the raw token."""
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            response = await client.post(
                "/jwt/login",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={"username": self._username, "password": self._password},
            )
            response.raise_for_status()
            self._cookies = dict(client.cookies)  # AR-JWT + route session cookies
            return response.text.strip()

    async def _get_token(self) -> str:
        """Return the cached token, fetching a new one if the cache is empty."""
        if self._token is None:
            async with self._lock:
                if self._token is None:  # re-check after acquiring the lock
                    self._token = await self._fetch_token()
        return self._token

    def invalidate(self) -> None:
        """Discard the cached token so the next request triggers a fresh fetch."""
        self._token = None
        self._cookies = {}

    async def async_auth_flow(
        self, request: httpx.Request
    ) -> AsyncGenerator[httpx.Request, httpx.Response]:
        token = await self._get_token()
        request.headers["Authorization"] = f"AR-JWT{token}"
        if self._cookies:
            request.headers["Cookie"] = "; ".join(
                f"{k}={v}" for k, v in self._cookies.items()
            )
        response = yield request

        if response.status_code == 401:
            logger.info("BMC Helix token rejected (401) — refreshing and retrying.")
            async with self._lock:
                self._token = await self._fetch_token()
            request.headers["Authorization"] = f"AR-JWT{self._token}"
            if self._cookies:
                request.headers["Cookie"] = "; ".join(
                    f"{k}={v}" for k, v in self._cookies.items()
                )
            yield request


def _parse_bmc_errors(response: HttpResponse) -> list[BmcHelixError]:
    """Parse the BMC Helix error list from a 4xx/5xx response body."""
    try:
        data = response.json
        if isinstance(data, list):
            return [
                BmcHelixError(
                    message_type=item.get("messageType", ""),
                    message_text=item.get("messageText", ""),
                    message_number=item.get("messageNumber", 0),
                    message_appended_text=item.get("messageAppendedText", ""),
                )
                for item in data
            ]
    except Exception as exc:
        logger.warning(
            "Failed to parse BMC Helix error response: %s", response.text, exc_info=exc
        )
    return []


_INCIDENT_FIELDS = (
    "Incident Number,Status,Submit Date,Priority,Impact,Urgency,"
    "Assigned Group,Assignee,Description,Detailed Decription,"
    "Categorization Tier 1,Categorization Tier 2,Categorization Tier 3,"
    "Product Categorization Tier 1,Product Categorization Tier 2,"
    "Product Categorization Tier 3,Product Name"
)


def _to_bmc_payload(incident: CreateIncidentInput) -> dict:
    """Map a domain CreateIncidentInput to the BMC Helix REST API payload."""
    return {
        "Assigned Group": incident.assigned_group,
        "Assigned Support Company": incident.assigned_support_company,
        "Assigned Support Organization": incident.assigned_support_organization,
        "Assignee": incident.assignee,
        "Categorization Tier 1": incident.categorization_tier_1,
        "Categorization Tier 2": incident.categorization_tier_2,
        "Categorization Tier 3": incident.categorization_tier_3,
        "Company": incident.company,
        "Description": incident.title,
        "Detailed_Decription": incident.description,
        "Direct Contact First Name": incident.direct_contact_first_name,
        "Direct Contact Last Name": incident.direct_contact_last_name,
        "First_Name": incident.first_name,
        "Impact": incident.impact,
        "Last_Name": incident.last_name,
        "Manufacturer": incident.manufacturer,
        "Product Categorization Tier 1": incident.product_categorization_tier_1,
        "Product Categorization Tier 2": incident.product_categorization_tier_2,
        "Product Categorization Tier 3": incident.product_categorization_tier_3,
        "Reported Source": incident.reported_source,
        "Service_Type": incident.service_type,
        "Status": incident.status,
        "Urgency": incident.urgency,
        "z1D_Action": incident.action,
    }


class BmcHelixAdapter(BmcHelixPort):
    def __init__(self, client: HttpClient, auth: BmcHelixAuth) -> None:
        self._client = client
        self._auth = auth

    async def stop(self) -> None:
        await self._client.close()

    async def fetch_token(self) -> str:
        """Return the current cached JWT, fetching a new one if necessary."""
        return await self._auth._get_token()

    def build_request_payload(self, payload: CreateIncidentInput) -> dict:
        return _to_bmc_payload(payload)

    async def create_incident(self, payload: CreateIncidentInput) -> IncidentResponse:
        """Create an incident in BMC Helix and return the created entry."""
        params = {"fields": "values(Incident Number,Request ID)"}
        bmc_payload = {"values": _to_bmc_payload(payload)}
        logger.info("Creating incident in BMC Helix - payload: %s", bmc_payload)
        try:
            response = await self._client.post(
                "/arsys/v1/entry/HPD:IncidentInterface_Create",
                json=bmc_payload,
                params=params,
            )
        except HttpClientError as exc:
            response = exc.response
            if response:
                bmc_errors = _parse_bmc_errors(response)
                raise IncidentCreationError(
                    f"BMC Helix returned {response.status_code} while creating the incident.",
                    bmc_errors=bmc_errors,
                ) from exc
            raise

        data = response.json
        logger.debug("Create incident response data: %s", data)
        values = data["values"]
        incident_id = values.get("Incident Number", "")
        if not incident_id:
            raise IncidentCreationError(
                "BMC Helix did not return an incident number after creation."
            )
        logger.info("Incident ID created: %s", incident_id)

        return IncidentResponse(
            incident_number=incident_id,
            request_id=values.get("Request ID", ""),
        )

    async def get_incident(self, incident_number: str) -> IncidentInfo:
        """Query a single incident from BMC Helix by its incident number."""
        params = {
            "q": f"'Incident Number'=\"{incident_number}\"",
            "fields": f"values({_INCIDENT_FIELDS})",
        }
        try:
            response = await self._client.get(
                "/arsys/v1/entry/HPD:Help Desk/",
                params=params,
            )
        except HttpClientError as exc:
            response = exc.response
            if response:
                bmc_errors = _parse_bmc_errors(response)
                raise BmcHelixClientError(
                    f"BMC Helix did not return data for incident '{incident_number}'.",
                    status_code=response.status_code,
                    bmc_errors=bmc_errors,
                ) from exc
            raise

        data = response.json
        entries = data.get("entries", [])
        if not entries:
            raise BmcHelixClientError(
                f"Incident '{incident_number}' not found in BMC Helix.",
                status_code=404,
            )
        values = entries[0].get("values", {})
        logger.debug("Get incident response data: %s", data)

        if not values:
            raise BmcHelixClientError(
                f"Incident '{incident_number}' not found in BMC Helix.",
                status_code=404,
            )

        return IncidentInfo(
            assigned_group=values.get("Assigned Group", ""),
            assignee=values.get("Assignee", ""),
            categorization_tier_1=values.get("Categorization Tier 1", ""),
            categorization_tier_2=values.get("Categorization Tier 2", ""),
            categorization_tier_3=values.get("Categorization Tier 3", ""),
            description=values.get("Description", ""),
            detailed_description=values.get("Detailed Decription", ""),
            incident_number=values.get("Incident Number", ""),
            impact=values.get("Impact", ""),
            priority=values.get("Priority", ""),
            product_categorization_tier_1=values.get(
                "Product Categorization Tier 1", ""
            ),
            product_categorization_tier_2=values.get(
                "Product Categorization Tier 2", ""
            ),
            product_categorization_tier_3=values.get(
                "Product Categorization Tier 3", ""
            ),
            product_name=values.get("Product Name", ""),
            status=values.get("Status", ""),
            submit_date=values.get("SubmitDate", ""),
            urgency=values.get("Urgency", ""),
        )

    @classmethod
    def build(
        cls, base_url: str, username: str, password: str, timeout: float = 30.0
    ) -> "BmcHelixAdapter":
        """Factory method — builds the adapter with BMC Helix auth wired into the HTTP client."""
        auth = BmcHelixAuth(base_url, username, password)
        http_client = HttpClient(
            base_url=base_url,
            auth=auth,
            timeout=timeout,
        )
        return cls(http_client, auth)
