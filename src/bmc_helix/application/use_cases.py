import dataclasses

from src.bmc_helix.domain.entities import (
    CreateIncidentInput,
    IncidentInfo,
    IncidentResponse,
    Transaction,
    TransactionStatus,
)
from src.bmc_helix.domain.exceptions import IncidentCreationError
from src.bmc_helix.domain.ports import BmcHelixPort
from src.bmc_helix.domain.repositories import TransactionRepositoryPort


class CreateIncidentUseCase:
    def __init__(
        self, adapter: BmcHelixPort, repository: TransactionRepositoryPort
    ) -> None:
        self._adapter = adapter
        self._repository = repository

    async def execute(
        self,
        payload: CreateIncidentInput,
        service_code: str | None = None,
        event_id: str | None = None,
    ) -> IncidentResponse:
        transaction = await self._repository.create(
            Transaction(
                service_code=service_code,
                event_id=event_id,
                status=TransactionStatus.PENDING,
                request=self._adapter.build_request_payload(payload),
            )
        )
        try:
            response = await self._adapter.create_incident(payload)
        except IncidentCreationError as exc:
            transaction.status = TransactionStatus.ERROR
            transaction.response = {"error": str(exc)}
            await self._repository.update(transaction)
            raise

        transaction.status = TransactionStatus.SUCCESS
        transaction.incident_id = response.incident_number
        transaction.response = dataclasses.asdict(response)
        await self._repository.update(transaction)
        return response


class GetIncidentUseCase:
    def __init__(self, adapter: BmcHelixPort) -> None:
        self._adapter = adapter

    async def execute(self, incident_number: str) -> IncidentInfo:
        return await self._adapter.get_incident(incident_number)
