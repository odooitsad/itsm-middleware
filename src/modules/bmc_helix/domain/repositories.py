from typing import Protocol

from src.modules.bmc_helix.domain.entities import (
    OperationalCategorization,
    ProductCategorization,
    Transaction,
)


class TransactionRepositoryPort(Protocol):
    async def get(self, transaction_id: int) -> Transaction | None: ...
    async def create(self, transaction: Transaction) -> Transaction: ...
    async def update(self, transaction: Transaction) -> Transaction: ...


class CategorizationsRepositoryPort(Protocol):
    async def get_operational_categorization(
        self, id: int
    ) -> OperationalCategorization | None: ...
    async def get_product_categorization(
        self, id: int
    ) -> ProductCategorization | None: ...
