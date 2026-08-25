from dataclasses import asdict

from src.core.logger import get_logger
from src.modules.freya.application.notification_templates import (
    build_im_closed_template,
    build_im_created_success_template,
    build_im_creation_failure_template,
)
from src.modules.freya.domain.entities import (
    CloseIMInput,
    CreateIMInput,
    IMResult,
    IMStatus,
    Transaction,
    TransactionStatus,
    UpdateIMInput,
)
from src.modules.freya.domain.exceptions import DomainException, FreyaClientError
from src.modules.freya.domain.ports import (
    FreyaPort,
    NotificationPort,
    TroubleshootingPort,
)
from src.modules.freya.domain.repositories import TransactionRepositoryPort

logger = get_logger(__name__)


def _build_create_im_payload(payload: CreateIMInput) -> dict:
    return {
        "Area": payload.area,
        "Categoria": payload.category,
        "CiAfectado": payload.affected_ci,
        "CiOperativo": payload.ci_is_operational,
        "Descripcion": payload.description,
        "IdEvento": payload.event_id,
        "Impacto": payload.impact,
        "InitService": payload.init_service,
        "Origen": payload.origin,
        "SubCategoria": payload.sub_category,
        "Titulo": payload.title,
        "Urgencia": payload.urgency,
    }


def _build_update_im_payload(payload: UpdateIMInput) -> dict:
    return {
        "ImExistente": payload.existing_im,
        "NotaTrabajo": payload.working_note,
        "Tipo": payload.type,
    }


def _build_close_im_payload(payload: CloseIMInput) -> dict:
    return {
        "IdIm": payload.im_id,
        "FechaFinInterrupcionDeServicio": payload.service_end_date,
    }


def _build_create_transaction(payload: dict, host_id: int | None) -> Transaction:
    return Transaction(
        service_code=payload["CiAfectado"],
        event_id=payload["IdEvento"],
        im_id=None,
        hostid=host_id,
        request=payload,
        response=None,
    )


def _extract_im_number(result: str) -> str:
    im_index = result.find("IM")
    if im_index == -1:
        logger.warning("Unexpected response while creating IM: %s", result)
        raise FreyaClientError("Unexpected response while creating the IM")
    return result[im_index:]


class FreyaBaseUseCase:
    def __init__(
        self,
        adapter: FreyaPort,
        notifier: NotificationPort,
        repository: TransactionRepositoryPort,
        troubleshooting: TroubleshootingPort,
    ) -> None:
        self._adapter = adapter
        self._notifier = notifier
        self._transaction = repository
        self._troubleshooting = troubleshooting

    async def _finalize_incident_closure(
        self, body: dict, transaction: Transaction
    ) -> IMResult:
        im_id = body["IdIm"]
        result = await self._adapter.send_post_request("ResolvedIM", body)
        transaction.status_im = IMStatus.CLOSED
        await self._transaction.update(transaction)
        logger.info("%s resolved", im_id)
        return IMResult(detail=result, im=im_id)


class FreyaUseCase(FreyaBaseUseCase):
    async def create_im(
        self, payload: CreateIMInput, host_id: int | None = None
    ) -> IMResult:
        body = _build_create_im_payload(payload)
        transaction = await self._transaction.create(
            _build_create_transaction(body, host_id)
        )
        logger.info("Transaction %s - Creating IM: %s", transaction.id, body)
        try:
            result = await self._adapter.send_post_request("CreateIM", body)
        except Exception as exc:
            transaction.status = TransactionStatus.ERROR
            transaction.response = {"error": str(exc)}
            await self._transaction.update(transaction)
            raise

        im = _extract_im_number(result)
        logger.info("IM created: %s - CI: %s", im, payload.affected_ci)
        im_result = IMResult(detail="Incident created successfully", im=im)

        transaction.status = TransactionStatus.SUCCESS
        transaction.status_im = IMStatus.OPEN
        transaction.im_id = im
        transaction.response = im_result.__dict__
        await self._transaction.update(transaction)
        return im_result

    async def update_im(self, payload: UpdateIMInput) -> IMResult:
        body = _build_update_im_payload(payload)
        im = payload.existing_im
        logger.info("Adding working note to %s", im)
        result = await self._adapter.send_post_request("UpdateIm", body)
        logger.info(
            "Working note added to %s: %s...", im, payload.working_note[0][:200]
        )
        return IMResult(detail=result, im=im)

    async def close_im(self, payload: CloseIMInput) -> IMResult:
        im_id = payload.im_id
        transaction = await self._transaction.get_by_im_id(im_id)
        if transaction is None:
            logger.error("Transaction with ID %s not found while closing IM", im_id)
            raise FreyaClientError(f"No transaction with ID {im_id}", status_code=404)

        body = _build_close_im_payload(payload)
        logger.info("Resolving IM - transaction %s - %s", transaction.id, body)
        return await self._finalize_incident_closure(body, transaction)


class FreyaFromZabbixUseCase(FreyaBaseUseCase):
    """A FreyaUseCase variant that closes IMs from Zabbix."""

    async def create_pending_im(
        self, payload: CreateIMInput, host_id: int | None = None
    ) -> int:
        """Persist a PENDING transaction and return its id without calling Freya."""
        body = _build_create_im_payload(payload)
        transaction = await self._transaction.create(
            _build_create_transaction(body, host_id)
        )
        logger.info(f"Pending IM transaction created: {transaction.id}")
        if transaction.id is None:
            raise DomainException("Transaction was created without an id.")
        return transaction.id

    async def process_pending_im(
        self, transaction_id: int, payload: CreateIMInput, zabbix_event_dict
    ) -> None:
        """Call Freya for a transaction created via create_pending_im.

        Meant to run as a fire-and-forget background task, so errors are
        logged and recorded on the transaction rather than raised.
        """
        transaction = await self._transaction.get(transaction_id)
        if transaction is None:
            logger.error("Transaction %s not found for pending IM", transaction_id)
            return

        body = _build_create_im_payload(payload)
        logger.info("Transaction %s - Creating IM: %s", transaction_id, body)
        try:
            result = await self._adapter.send_post_request("CreateIM", body)
        except Exception as exc:  # noqa
            transaction.status = TransactionStatus.ERROR
            transaction.response = {"error": str(exc)}
            await self._transaction.update(transaction)
            template = build_im_creation_failure_template(**zabbix_event_dict)
            await self._notifier.notify_via_telegram(template)
            return

        im = _extract_im_number(result)
        logger.info("IM created: %s - transaction %s", im, transaction_id)

        transaction.status = TransactionStatus.SUCCESS
        transaction.status_im = IMStatus.OPEN
        transaction.im_id = im
        transaction.response = {"detail": "IM created successfully", "im": im}
        await self._transaction.update(transaction)

        if zabbix_event_dict.get("run_tshoot"):
            await self._troubleshooting.execute(
                im_id=im, ip_wan=zabbix_event_dict["ip_wan"]
            )

        template = build_im_created_success_template(**zabbix_event_dict, im_id=im)
        await self._notifier.notify_via_telegram(template)

    async def close_im_from_zabbix(
        self, payload: CloseIMInput, transaction_id: int, zabbix_event_dict
    ) -> IMResult:
        transaction = await self._transaction.get(transaction_id)
        if transaction is None:
            msg = f"Transaction with id {transaction_id} not found while closing IM"
            logger.error(msg)
            raise FreyaClientError(msg, status_code=404)

        payload.im_id = transaction.im_id or ""
        body = _build_close_im_payload(payload)
        logger.info(
            "Resolving IM from zabbix - transaction %s - %s", transaction.id, body
        )
        template = build_im_closed_template(**zabbix_event_dict, **asdict(payload))
        await self._notifier.notify_via_telegram(template)
        return await self._finalize_incident_closure(body, transaction)
