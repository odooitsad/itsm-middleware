from src.bmc_helix.domain.entities import IncidentResponse
from src.bmc_helix.domain.ports import BmcHelixPort


class CreateIncidentUseCase:
    def __init__(self, adapter: BmcHelixPort) -> None:
        self._adapter = adapter

    async def execute(self, payload: dict[str, str]) -> IncidentResponse:
        response = await self._adapter.create_incident({"values": payload})
        print(f"Create incident response: {response}")
        return response
