from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TransactionStatus(str, Enum):
    PENDING = "En proceso"
    SUCCESS = "Procesado"
    ERROR = "Procesado con error"


@dataclass
class Transaction:
    service_code: str | None
    event_id: str | None
    status: TransactionStatus
    ticket_number: str | None = None
    request: dict | None = None
    response: dict | None = None
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class CreateTicketInput:
    email_subject: str
    description: str
    failure_start_date: str
    priority: int
    impact_level: int
    origin_ids: list[int]
    tag_ids: list[int]


@dataclass
class CreateTicketOut:
    ticket_id: int
    ticket_number: str


@dataclass
class CloseTicketInput:
    ticket_number: str
    failure_end_date: str
    root_cause: str
    issue_update: str
    notification_chat_date: str
    evidence_notification: str
    escalation_requested_date: str
    evidence_escalation_request: str
    ssh_user_ids: list[int]


@dataclass
class CloseTicketOut:
    status: str
    message: str
    ticket_id: int
    ticket_number: str
    closed_by: str
    closed_date: str
    stage: str
