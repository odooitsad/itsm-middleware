from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.freya.domain.entities import IMStatus, Transaction, TransactionStatus
from src.modules.freya.domain.exceptions import DomainException
from src.modules.freya.domain.repositories import TransactionRepositoryPort
from src.modules.freya.infrastructure.models import TransactionModel


class TransactionRepository(TransactionRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, transaction_id: int) -> Transaction | None:
        model = await self._session.get(TransactionModel, transaction_id)
        return _to_entity(model) if model is not None else None

    async def get_by_im_id(self, im_id: str) -> Transaction | None:
        result = await self._session.execute(
            select(TransactionModel).where(TransactionModel.im_id == im_id)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def create(self, transaction: Transaction) -> Transaction:
        model = _to_model(transaction)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        await self._session.commit()
        return _to_entity(model)

    async def update(self, transaction: Transaction) -> Transaction:
        if transaction.id is None:
            raise DomainException("Cannot update a Transaction without an id.")
        model = await self._session.get(TransactionModel, transaction.id)
        if model is None:
            raise DomainException(f"Transaction {transaction.id} not found.")
        model.service_code = transaction.service_code
        model.event_id = transaction.event_id
        model.status = transaction.status.value
        model.status_im = transaction.status_im.value
        model.im_id = transaction.im_id
        model.hostid = transaction.hostid
        model.request = transaction.request
        model.response = transaction.response
        await self._session.flush()
        await self._session.refresh(model)
        await self._session.commit()
        return _to_entity(model)


def _to_entity(model: TransactionModel) -> Transaction:
    return Transaction(
        id=model.id,
        created_at=model.created_at,
        service_code=model.service_code,
        event_id=model.event_id,
        status=TransactionStatus(model.status),
        status_im=IMStatus(model.status_im),
        im_id=model.im_id,
        hostid=model.hostid,
        request=model.request,
        response=model.response,
    )


def _to_model(transaction: Transaction) -> TransactionModel:
    return TransactionModel(
        service_code=transaction.service_code,
        event_id=transaction.event_id,
        status=transaction.status.value,
        status_im=transaction.status_im.value,
        im_id=transaction.im_id,
        hostid=transaction.hostid,
        request=transaction.request,
        response=transaction.response,
    )
