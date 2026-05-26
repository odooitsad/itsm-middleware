from src.bmc_helix.domain.entities import (
    CreateIncidentInput,
    IncidentInfo,
    IncidentResponse,
)
from src.bmc_helix.domain.exceptions import IncidentNotFoundError
from src.bmc_helix.domain.ports import BmcHelixPort
from src.core.clients.httpx import HttpxClient
from src.core.logger import get_logger

logger = get_logger(__name__)

_INCIDENT_FIELDS = (
    "Incident Number,Status,Submit Date,Priority,Impact,Urgency,"
    "Assigned Group,Assignee,Description,Detailed Decription,"
    "Categorization Tier 1,Categorization Tier 2,Categorization Tier 3,"
    "Product Categorization Tier 1,Product Categorization Tier 2,"
    "Product Categorization Tier 3,Product Name"
)

# BMC Helix fixed fields — injected into every incident payload.
_BMC_DEFAULTS: dict[str, str] = {
    "Company": "CENIT",
    "Direct Contact First Name": "Integracion",
    "Direct Contact Last Name": "Datasmart",
    "First_Name": "Integracion",
    "Last_Name": "Datasmart",
    "Reported Source": "Self Service",
    "Status": "Assigned",
    "z1D_Action": "CREATE",
}


def _to_bmc_payload(incident: CreateIncidentInput) -> dict:
    """Map a domain CreateIncidentInput to the BMC Helix REST API payload."""
    return {
        **_BMC_DEFAULTS,
        "Assigned Group": incident.assigned_group,
        "Assigned Support Company": incident.assigned_support_company,
        "Assigned Support Organization": incident.assigned_support_organization,
        "Assignee": incident.assignee,
        "Categorization Tier 1": incident.categorization_tier_1,
        "Categorization Tier 2": incident.categorization_tier_2,
        "Categorization Tier 3": incident.categorization_tier_3,
        "Description": incident.description,
        "Detailed_Decription": incident.detailed_description,
        "Impact": incident.impact,
        "Manufacturer": incident.manufacturer,
        "Product Categorization Tier 1": incident.product_categorization_tier_1,
        "Product Categorization Tier 2": incident.product_categorization_tier_2,
        "Product Categorization Tier 3": incident.product_categorization_tier_3,
        "Urgency": incident.urgency,
        "Service_Type": incident.service_type,
    }


class BmcHelixAdapter(BmcHelixPort):
    def __init__(self, client: HttpxClient, username: str, password: str) -> None:
        self._client = client
        self.username = username
        self.password = password

    async def stop(self) -> None:
        await self._client.close()

    async def fetch_token(self) -> str:
        """
        Authenticate against the BMC Helix API and return the JWT token.
        Assuming the token is returned as plain text.
        """
        response = await self._client.post(
            "/jwt/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"username": self.username, "password": self.password},
        )
        token = response.text.strip()
        return token

    def build_request_payload(self, payload: CreateIncidentInput) -> dict:
        return _to_bmc_payload(payload)

    async def create_incident(self, payload: CreateIncidentInput) -> IncidentResponse:
        """Create an incident in BMC Helix and return the created entry."""
        token = await self.fetch_token()
        params = {"fields": "values(Incident Number,Request ID)"}
        bmc_payload = {"values": _to_bmc_payload(payload)}
        response = await self._client.post(
            "/arsys/v1/entry/HPD:IncidentInterface_Create",
            headers={"Authorization": f"AR-JWT{token}"},
            json=bmc_payload,
            params=params,
        )
        data = response.json()
        values = data["values"]
        logger.debug(f"Create incident response data: {data}")

        return IncidentResponse(
            incident_number=values.get("Incident Number", ""),
            request_id=values.get("Request ID", ""),
        )

    async def get_incident(self, incident_number: str) -> IncidentInfo:
        """Query a single incident from BMC Helix by its incident number."""
        token = await self.fetch_token()
        params = {"fields": f"values({_INCIDENT_FIELDS})"}
        response = await self._client.get(
            f"/arsys/v1/entry/HPD:Help Desk/{incident_number}",
            headers={"Authorization": f"AR-JWT{token}"},
            params=params,
        )
        data = response.json()
        logger.debug(f"Get incident response data: {data}")

        values = data.get("values", {})
        if not values:
            raise IncidentNotFoundError(
                f"Incident '{incident_number}' not found in BMC Helix."
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
        """Factory method — builds the HttpxClient with BMC Helix auth config."""
        http_client = HttpxClient(
            base_url=base_url,
            timeout=timeout,
        )
        return cls(http_client, username, password)
