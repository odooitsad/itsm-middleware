from src.bmc_helix.domain.entities import CreateIncidentInput, IncidentResponse
from src.bmc_helix.domain.ports import BmcHelixPort
from src.core.clients.httpx import HttpxClient
from src.core.logger import get_logger

logger = get_logger(__name__)

# BMC Helix fixed fields — injected into every incident payload.
_BMC_DEFAULTS: dict[str, str] = {
    "First_Name": "Integracion",
    "Last_Name": "Datasmart",
    "Company": "CENIT",
    "Direct Contact First Name": "Integracion",
    "Direct Contact Last Name": "Datasmart",
    "Status": "Assigned",
    "Reported Source": "Self Service",
    "z1D_Action": "CREATE",
}


def _to_bmc_payload(incident: CreateIncidentInput) -> dict:
    """Map a domain CreateIncidentInput to the BMC Helix REST API payload."""
    return {
        **_BMC_DEFAULTS,
        "Description": incident.description,
        "Detailed_Decription": incident.detailed_description,
        "Impact": incident.impact,
        "Urgency": incident.urgency,
        "Service_Type": incident.service_type,
        "Categorization Tier 1": incident.categorization_tier_1,
        "Categorization Tier 2": incident.categorization_tier_2,
        "Categorization Tier 3": incident.categorization_tier_3,
        "Product Categorization Tier 1": incident.product_categorization_tier_1,
        "Product Categorization Tier 2": incident.product_categorization_tier_2,
        "Product Categorization Tier 3": incident.product_categorization_tier_3,
        "Manufacturer": incident.manufacturer,
        "Assigned Support Company": incident.assigned_support_company,
        "Assigned Support Organization": incident.assigned_support_organization,
        "Assigned Group": incident.assigned_group,
        "Assignee": incident.assignee,
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
