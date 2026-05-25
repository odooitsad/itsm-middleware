from sqlalchemy.ext.asyncio import AsyncSession

from src.bmc_helix.domain.entities import Transaction, TransactionStatus
from src.bmc_helix.domain.exceptions import DomainException
from src.bmc_helix.infrastructure.models import TransactionModel


class TransactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, transaction_id: int) -> Transaction | None:
        model = await self._session.get(TransactionModel, transaction_id)
        return _to_entity(model) if model is not None else None

    async def create(self, transaction: Transaction) -> Transaction:
        model = _to_model(transaction)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def update(self, transaction: Transaction) -> Transaction:
        if transaction.id is None:
            raise DomainException("Cannot update a Transaction without an id.")
        model = await self._session.get(TransactionModel, transaction.id)
        if model is None:
            raise DomainException(f"Transaction {transaction.id} not found.")
        model.status = transaction.status.value
        model.incident_id = transaction.incident_id
        model.response = transaction.response
        model.service_code = transaction.service_code
        model.event_id = transaction.event_id
        model.request = transaction.request
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)


def _to_entity(model: TransactionModel) -> Transaction:
    return Transaction(
        id=model.id,
        created_at=model.created_at,
        updated_at=model.updated_at,
        service_code=model.service_code,
        event_id=model.event_id,
        status=TransactionStatus(model.status),
        incident_id=model.incident_id,
        request=model.request,
        response=model.response,
    )


def _to_model(transaction: Transaction) -> TransactionModel:
    return TransactionModel(
        service_code=transaction.service_code,
        event_id=transaction.event_id,
        status=transaction.status.value,
        incident_id=transaction.incident_id,
        request=transaction.request,
        response=transaction.response,
    )
