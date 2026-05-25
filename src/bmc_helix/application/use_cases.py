from src.bmc_helix.domain.entities import CreateIncidentInput, IncidentResponse
from src.bmc_helix.domain.ports import BmcHelixPort


class CreateIncidentUseCase:
    def __init__(self, adapter: BmcHelixPort) -> None:
        self._adapter = adapter

    async def execute(self, payload: CreateIncidentInput) -> IncidentResponse:
        response = await self._adapter.create_incident(payload)
        return response
