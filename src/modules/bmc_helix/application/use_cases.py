import dataclasses

from src.modules.bmc_helix.domain.entities import (
    CreateIncidentInput,
    CreateIncidentInputZabbix,
    IncidentResponse,
    Transaction,
    TransactionStatus,
)
from src.modules.bmc_helix.domain.exceptions import IncidentCreationError
from src.modules.bmc_helix.domain.ports import BmcHelixPort
from src.modules.bmc_helix.domain.repositories import (
    CategorizationsRepositoryPort,
    TransactionRepositoryPort,
)


def _build_create_incident_input_from_zabbix(
    payload: CreateIncidentInputZabbix,
    operationat_cat: dict,
    product_cat: dict,
) -> CreateIncidentInput:
    payload_dict = payload.to_input_dict()
    description = payload_dict.pop("base_description") + operationat_cat.pop(
        "description", ""
    )
    return CreateIncidentInput(
        description=description,
        **operationat_cat,
        **product_cat,
        **payload_dict,
    )


class CreateIncidentUseCase:
    def __init__(
        self,
        adapter: BmcHelixPort,
        transaction_repo: TransactionRepositoryPort,
        categorization_repo: CategorizationsRepositoryPort,
    ) -> None:
        self._adapter = adapter
        self._transaction_repo = transaction_repo
        self._categorization_repo = categorization_repo

    async def execute(self, payload: CreateIncidentInput) -> IncidentResponse:
        transaction = await self._transaction_repo.create(
            Transaction(request=self._adapter.build_request_payload(payload))
        )
        return await self._finalize_incident_creation(transaction, payload)

    async def execute_from_zabbix(
        self, payload: CreateIncidentInputZabbix
    ) -> IncidentResponse:
        operational_cat_id = payload.operational_categorization_id
        operationat_cat = (
            await self._categorization_repo.get_operational_categorization(
                operational_cat_id
            )
        )
        if operationat_cat is None:
            raise IncidentCreationError(
                f"Operational categorization with id {operational_cat_id} not found."
            )

        product_cat_id = payload.product_categorization_id
        product_cat = await self._categorization_repo.get_product_categorization(
            product_cat_id
        )
        if product_cat is None:
            raise IncidentCreationError(
                f"Product categorization with id {product_cat_id} not found."
            )
        body = _build_create_incident_input_from_zabbix(
            payload, operationat_cat.to_input_dict(), dataclasses.asdict(product_cat)
        )
        transaction = await self._transaction_repo.create(
            Transaction(
                event_id=payload.event_id,
                request=self._adapter.build_request_payload(body),
                service_code=payload.service_code,
            )
        )
        return await self._finalize_incident_creation(transaction, body)

    async def _finalize_incident_creation(
        self, transaction: Transaction, body: CreateIncidentInput
    ) -> IncidentResponse:
        try:
            response = await self._adapter.create_incident(body)
        except IncidentCreationError as exc:
            transaction.status = TransactionStatus.ERROR
            transaction.response = {"error": str(exc)}
            await self._transaction_repo.update(transaction)
            raise

        transaction.status = TransactionStatus.SUCCESS
        transaction.incident_id = response.incident_number
        transaction.response = dataclasses.asdict(response)
        await self._transaction_repo.update(transaction)
        return response
