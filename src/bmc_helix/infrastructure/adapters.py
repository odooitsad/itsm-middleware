from src.bmc_helix.domain.entities import IncidentResponse
from src.bmc_helix.domain.ports import BmcHelixPort
from src.core.clients.httpx import HttpxClient
from src.core.logger import get_logger

logger = get_logger(__name__)


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

    async def create_incident(self, payload: dict) -> IncidentResponse:
        """Create an incident in BMC Helix and return the created entry."""
        token = await self.fetch_token()
        params = {"fields": "values(Incident Number,Request ID)"}
        response = await self._client.post(
            "/arsys/v1/entry/HPD:IncidentInterface_Create",
            headers={"Authorization": f"AR-JWT{token}"},
            json=payload,
            params=params,
        )
        data = response.json()
        values = data["values"]
        logger.debug(f"Create incident response data: {data}")

        # TODO: Map the response to the IncidentResponse entity properly, this is a simplified example
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
