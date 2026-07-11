import httpx

from src.core.clients.httpx import HttpxClient
from src.core.logger import get_logger
from src.modules.its_helpdesk.domain.entities import (
    CloseTicketInput,
    CloseTicketOut,
    CreateTicketInput,
    CreateTicketOut,
)
from src.modules.its_helpdesk.domain.exceptions import TicketCreationError
from src.modules.its_helpdesk.domain.ports import ItsHelpdeskPort

logger = get_logger(__name__)


def _jsonrpc_body(jsonrpc_id: int, params: dict) -> dict:
    return {"jsonrpc": "2.0", "method": "call", "id": jsonrpc_id, "params": params}


def _create_input_to_odoo_params(ticket: CreateTicketInput) -> dict:
    return {
        "email_subject": ticket.email_subject,
        "inicio_falla": ticket.failure_start_date,
        "description_custom": ticket.description,
        "priority": ticket.priority,
        "nivel_afectacion": ticket.impact_level,
        "origen_ids": ticket.origin_ids,
        "tag_ids": ticket.tag_ids,
    }


def _close_input_to_odoo_params(ticket: CloseTicketInput) -> dict:
    return {
        "ticket_number": ticket.ticket_number,
        "fin_falla": ticket.failure_end_date,
        "problema_raiz": ticket.root_cause,
        "afectacion_update": ticket.issue_update,
        "notification_chat_date": ticket.notification_chat_date,
        "evidence_notification": ticket.evidence_notification,
        "escalation_requested_date": ticket.escalation_requested_date,
        "evidence_escalation_request": ticket.evidence_escalation_request,
        "ssh_user_ids": ticket.ssh_user_ids,
    }


class ItsHelpdeskAdapter(ItsHelpdeskPort):
    def __init__(
        self,
        client: HttpxClient,
        db_name: str,
        username: str,
        password: str,
        jsonrpc_id: int,
    ) -> None:
        self._client = client
        self._db_name = db_name
        self._username = username
        self._password = password
        self._jsonrpc_id = jsonrpc_id

    @classmethod
    def build(
        cls,
        base_url: str,
        verify_ssl: bool,
        db_name: str,
        username: str,
        password: str,
        jsonrpc_id: int,
        timeout: float,
    ) -> "ItsHelpdeskAdapter":
        client = HttpxClient(base_url=base_url, timeout=timeout, verify=verify_ssl)
        return cls(client, db_name, username, password, jsonrpc_id)

    async def stop(self) -> None:
        await self._client.close()

    def build_request_payload(self, payload: CreateTicketInput) -> dict:
        return _create_input_to_odoo_params(payload)

    async def authenticate(self) -> None:
        params = {
            "db": self._db_name,
            "login": self._username,
            "password": self._password,
        }
        payload = _jsonrpc_body(self._jsonrpc_id, params)
        await self._client.post("/login", json=payload)

    def _validate_odoo_error(self, data: dict) -> None:
        if "error" in data:
            error = data.get("error", {})
            error_data = error.get("data", {})
            logger.error(
                "Ticket creation failed: %s", error_data.get("debug", "Unknown error")
            )
            raise TicketCreationError(
                f"ITS Helpdesk ticket creation error: {error.get('message', 'Unknown error')}"
            )

    async def create_ticket(self, payload: CreateTicketInput) -> CreateTicketOut:
        await self.authenticate()

        body = _jsonrpc_body(self._jsonrpc_id, _create_input_to_odoo_params(payload))
        logger.info("Creating ticket in ITS Helpdesk — payload params: %s", payload)

        try:
            response = await self._client.post("/tickets/create", json=body)
        except httpx.HTTPStatusError as exc:
            raise TicketCreationError(
                f"ITS Helpdesk returned {exc.response.status_code} while creating the ticket."
            ) from exc

        data = response.json()
        self._validate_odoo_error(data)

        result = data.get("result", {})
        if not result:
            msg = "Ticket creation failed: No result returned from ITS Helpdesk."
            logger.error("%s %s", msg, data)
            raise TicketCreationError(msg)

        if "error" in result:
            logger.error("Ticket creation failed: %s ", result)
            raise TicketCreationError("Ticket creation failed")

        logger.info("Ticket created: %s", result.get("ticket_number"))
        return CreateTicketOut(
            ticket_id=result["ticket_id"],
            ticket_number=result["ticket_number"],
        )

    async def close_ticket(self, payload: CloseTicketInput) -> CloseTicketOut:
        await self.authenticate()

        body = _jsonrpc_body(self._jsonrpc_id, _close_input_to_odoo_params(payload))
        logger.info("Closing ticket in ITS Helpdesk — params: %s", body)

        try:
            response = await self._client.post("/ticket/close", json=body)
        except httpx.HTTPStatusError as exc:
            raise TicketCreationError(
                f"ITS Helpdesk returned {exc.response.status_code} while closing the ticket."
            ) from exc

        data = response.json()
        self._validate_odoo_error(data)

        result = data.get("result", {})
        if not result:
            msg = "Ticket closure failed: No result returned from ITS Helpdesk."
            logger.error("%s %s", msg, data)
            raise TicketCreationError(msg)

        if "error" in result:
            logger.error("Ticket closure failed: %s ", result)
            raise TicketCreationError(f"Ticket closure failed: {result['error']}")

        logger.info("Ticket closed: %s", result.get("ticket_number"))
        return CloseTicketOut(
            status=result["status"],
            message=result["message"],
            ticket_id=result["ticket_id"],
            ticket_number=result["ticket_number"],
            closed_by=result["closed_by"],
            closed_date=result["close_date"],
            stage=result["stage"],
        )
