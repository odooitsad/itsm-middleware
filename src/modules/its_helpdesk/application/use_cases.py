import dataclasses

from src.modules.its_helpdesk.domain.entities import (
    CreateTicketInput,
    CreateTicketOut,
    Transaction,
    TransactionStatus,
)
from src.modules.its_helpdesk.domain.exceptions import TicketCreationError
from src.modules.its_helpdesk.domain.ports import ItsHelpdeskPort
from src.modules.its_helpdesk.domain.repositories import TransactionRepositoryPort


class CreateTicketUseCase:
    def __init__(
        self, adapter: ItsHelpdeskPort, repository: TransactionRepositoryPort
    ) -> None:
        self._adapter = adapter
        self._repository = repository

    async def execute(
        self,
        payload: CreateTicketInput,
        service_code: str | None = None,
        event_id: str | None = None,
    ) -> CreateTicketOut:
        transaction = await self._repository.create(
            Transaction(
                service_code=service_code,
                event_id=event_id,
                status=TransactionStatus.PENDING,
                request=self._adapter.build_request_payload(payload),
            )
        )
        try:
            response = await self._adapter.create_ticket(payload)
        except TicketCreationError as exc:
            transaction.status = TransactionStatus.ERROR
            transaction.response = {"error": str(exc)}
            await self._repository.update(transaction)
            raise

        transaction.status = TransactionStatus.SUCCESS
        transaction.ticket_number = response.ticket_number
        transaction.response = dataclasses.asdict(response)
        await self._repository.update(transaction)
        return response
