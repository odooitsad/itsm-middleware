from src.bmc_helix.domain.entities import CreateIncidentInput, IncidentResponse
from src.bmc_helix.domain.ports import BmcHelixPort
from src.bmc_helix.domain.repositories import TransactionRepositoryPort


class CreateIncidentUseCase:
    def __init__(
        self, adapter: BmcHelixPort, repository: TransactionRepositoryPort
    ) -> None:
        self._adapter = adapter
        self._repository = repository

    async def execute(self, payload: CreateIncidentInput) -> IncidentResponse:
        response = await self._adapter.create_incident(payload)
        return response
