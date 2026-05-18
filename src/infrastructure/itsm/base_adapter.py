from src.infrastructure.http.client import HttpxClient


class BaseITSMAdapter:
    """
    Base class for ITSM HTTP adapters.

    Receives a fully configured, already-started HttpxClient via dependency
    injection (from app.state). Concrete adapters implement the domain port
    contract and use self._http to make outbound calls.

    Example:

        class BmcHelixAdapter(BaseITSMAdapter):
            async def create_incident(self, alert: Alert) -> Ticket:
                data = await self._http.post("/api/arsys/v1/entry/HPD:IncidentInterface_Create", body={...})
                return _map_to_ticket(data)
    """

    def __init__(self, http_client: HttpxClient) -> None:
        self._http = http_client
