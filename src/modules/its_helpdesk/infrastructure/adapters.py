from src.core.clients.http import HttpClient, HttpResponse
from src.core.logger import get_logger
from src.modules.its_helpdesk.domain.entities import (
    CloseTicketInput,
    CloseTicketOut,
    CreateTicketInput,
    CreateTicketOut,
)
from src.modules.its_helpdesk.domain.exceptions import ItsHelpdeskClientError
from src.modules.its_helpdesk.domain.ports import ItsHelpdeskPort

logger = get_logger(__name__)


def _jsonrpc_body(jsonrpc_id: int, params: dict) -> dict:
    return {"jsonrpc": "2.0", "method": "call", "id": jsonrpc_id, "params": params}


# TODO: Consider getting data from DB
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
        client: HttpClient,
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
        client = HttpClient(base_url=base_url, timeout=timeout, verify=verify_ssl)
        return cls(client, db_name, username, password, jsonrpc_id)

    async def stop(self) -> None:
        await self._client.close()

    def build_request_payload(self, payload: CreateTicketInput) -> dict:
        return _create_input_to_odoo_params(payload)

    def _validate_response(self, response: HttpResponse, action: str) -> None:
        json_data = response.json
        error_msg = f"ITS Helpdesk {action} failed"

        if not json_data:
            logger.warning("Validation 1")
            logger.error("%s: %s", error_msg, response.text)
            raise ItsHelpdeskClientError(error_msg, 502)

        if "error" in json_data:
            logger.warning("Validation 2")
            logger.warning(json_data)
            message = (
                json_data.get("error", {})
                .get("data", {})
                .get("message", "Unknown error")
            )
            logger.error("%s: %s", error_msg, message)
            raise ItsHelpdeskClientError(f"{error_msg}: {message}", 400)

        result = json_data.get("result", {})
        if not result:
            logger.warning("Validation 3")
            logger.error("%s: %s", f"{error_msg} (No result)", json_data)
            raise ItsHelpdeskClientError(error_msg, 502)

        if "error" in result:
            logger.warning("Validation 4")
            detail = result.get("details") or result.get("error", "Unknown error")
            status_code = 401 if action == "authentication" else 400
            logger.error("%s - %s", error_msg, detail)
            raise ItsHelpdeskClientError(f"{error_msg} - {detail}", status_code)

    async def authenticate(self) -> None:
        params = {
            "db": self._db_name,
            "login": f"{self._username}",
            "password": self._password,
        }
        payload = _jsonrpc_body(self._jsonrpc_id, params)
        response = await self._client.post("/login", json=payload)

        self._validate_response(response, action="authentication")

    async def create_ticket(self, payload: CreateTicketInput) -> CreateTicketOut:
        await self.authenticate()
        body = _jsonrpc_body(self._jsonrpc_id, _create_input_to_odoo_params(payload))
        logger.info("Creating ticket in ITS Helpdesk — payload params: %s", body)

        response = await self._client.post("/tickets/create", json=body)
        self._validate_response(response, action="ticket creation")

        data = response.json
        result = data.get("result", {})

        logger.info("Ticket created: %s", result.get("ticket_number"))
        return CreateTicketOut(
            ticket_id=result["ticket_id"],
            ticket_number=result["ticket_number"],
        )

    async def close_ticket(self, payload: CloseTicketInput) -> CloseTicketOut:
        await self.authenticate()
        body = _jsonrpc_body(self._jsonrpc_id, _close_input_to_odoo_params(payload))
        logger.info("Closing ticket in ITS Helpdesk — params: %s", body)

        response = await self._client.post("/ticket/close", json=body)
        self._validate_response(response, action="ticket closure")

        data = response.json
        result = data.get("result", {})

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
