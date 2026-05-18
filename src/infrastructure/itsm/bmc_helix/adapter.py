from src.infrastructure.http.client import HttpxClient
from src.infrastructure.itsm.base_adapter import BaseITSMAdapter


class BmcHelixAdapter(BaseITSMAdapter):
    """
    BMC Helix ITSM adapter.

    Expects an HttpxClient configured with AuthType.JWT_FROM_API pointing at
    the BMC Helix REST API. The client is created in lifespan and injected
    via FastAPI dependencies.
    """

    def __init__(self, http_client: HttpxClient) -> None:
        super().__init__(http_client)
