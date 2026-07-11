from pydantic import BaseModel, Field

from src.core.base_schemas import ZabbixBase, ZabbixEventUrgency
from src.modules.its_helpdesk.domain.entities import CloseTicketInput, CreateTicketInput


class CreateTicketRequest(BaseModel):
    email_subject: str = Field(
        examples=["Caída Masiva Anillo Norte"],
        max_length=500,
    )
    description: str = Field(
        default="",
        examples=["<p>Alerta generada desde NOC Gateway...</p>"],
        description="HTML or plain-text description of the ticket",
    )
    failure_start_date: str = Field(
        examples=["2026-04-10 13:00:00"],
        description="Fault start datetime in format YYYY-MM-DD HH:MM:SS",
        max_length=50,
    )
    priority: int = Field(
        examples=[5],
        description="Numeric ID of the priority level in Odoo",
        ge=0,
    )
    impact_level: int = Field(
        examples=[5],
        description="Numeric ID of the impact level in Odoo",
        ge=0,
        le=5,
    )
    origin_ids: list[int] = Field(
        examples=[[4]],
        description="List of origin IDs (e.g. [4] for Zabbix)",
        min_length=1,
    )
    tag_ids: list[int] = Field(
        examples=[[45, 46]],
        description="List of fault-type tag IDs (e.g. [45, 46] for 'ICMP down' and 'falla de canal')",
        min_length=1,
    )

    def to_input(self) -> CreateTicketInput:
        return CreateTicketInput(
            email_subject=self.email_subject,
            failure_start_date=self.failure_start_date,
            priority=self.priority,
            impact_level=self.impact_level,
            origin_ids=self.origin_ids,
            tag_ids=self.tag_ids,
            description=self.description,
        )


class CreateTicketResponse(BaseModel):
    ticket_id: int
    ticket_number: str


class CloseTicketRequest(BaseModel):
    ticket_number: str = Field(
        examples=["TK-100726-0002"],
        max_length=50,
    )
    failure_end_date: str = Field(
        examples=["2026-04-10 14:00:00"],
        description="Fault end datetime in format YYYY-MM-DD HH:MM:SS",
        max_length=50,
    )
    root_cause: str = Field(max_length=1000)
    issue_update: str = Field(
        examples=["Se restableció el enlace de fibra óptica."],
        description="Update on the issue resolution",
        max_length=1000,
    )
    notification_chat_date: str = Field(
        examples=["2026-04-10 14:30:00"],
        max_length=50,
    )
    evidence_notification: str = Field(max_length=1000)
    escalation_requested_date: str = Field(
        examples=["2026-04-10 14:45:00"],
        max_length=50,
    )
    evidence_escalation_request: str = Field(max_length=1000)
    ssh_user_ids: list[int] = Field(
        examples=[[1]],
        description="List of SSH user IDs in Odoo",
        min_length=1,
    )

    def to_input(self) -> CloseTicketInput:
        return CloseTicketInput(
            ticket_number=self.ticket_number,
            failure_end_date=self.failure_end_date,
            root_cause=self.root_cause,
            issue_update=self.issue_update,
            notification_chat_date=self.notification_chat_date,
            evidence_notification=self.evidence_notification,
            escalation_requested_date=self.escalation_requested_date,
            evidence_escalation_request=self.evidence_escalation_request,
            ssh_user_ids=self.ssh_user_ids,
        )


class CloseTicketResponse(BaseModel):
    status: str
    message: str
    ticket_id: int
    ticket_number: str
    closed_by: str
    closed_date: str
    stage: str


# Zabbix-originated ticket schema

_URGENCY_TO_PRIORITY: dict[ZabbixEventUrgency, int] = {
    ZabbixEventUrgency.CRITICAL: 3,
    ZabbixEventUrgency.HIGH: 2,
    ZabbixEventUrgency.MEDIUM: 1,
    ZabbixEventUrgency.LOW: 0,
}


class ZabbixHelpdeskEvent(ZabbixBase):
    impact_level: int = Field(
        examples=[5],
        description="Numeric ID of the impact level in Odoo",
        ge=0,
    )
    origin_ids: list[int] = Field(
        examples=[[1]],
        description="List of origin IDs in Odoo (e.g. [1] for 'Alarma Zabbix')",
        min_length=1,
    )
    tag_ids: list[int] = Field(
        examples=[[1]],
        description="List of fault-type tag IDs in Odoo",
        min_length=1,
    )

    def to_input(self) -> CreateTicketInput:
        return CreateTicketInput(
            email_subject=self.title,
            failure_start_date=self.start_date,
            priority=_URGENCY_TO_PRIORITY[self.urgency],
            impact_level=self.impact_level,
            origin_ids=self.origin_ids,
            tag_ids=self.tag_ids,
            description=f"<p>{self.description}</p>",
        )
