from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TransactionStatus(str, Enum):
    PENDING = "En proceso"
    SUCCESS = "Procesado"
    ERROR = "Procesado con error"


@dataclass
class Transaction:
    id: int | None = None
    created_at: datetime | None = None
    event_id: str | None = None
    incident_id: str | None = None
    request: dict | None = None
    response: dict | None = None
    service_code: str | None = None
    status: TransactionStatus = TransactionStatus.PENDING
    updated_at: datetime | None = None


@dataclass(kw_only=True)
class OperationalCategorization:
    categorization_tier_1: str
    categorization_tier_2: str
    categorization_tier_3: str
    title: str
    assigned_group: str
    assignee: str
    description: str

    def to_input_dict(self) -> dict:
        return {
            "categorization_tier_1": self.categorization_tier_1,
            "categorization_tier_2": self.categorization_tier_2,
            "categorization_tier_3": self.categorization_tier_3,
            "assigned_group": self.assigned_group,
            "assignee": self.assignee,
            "description": self.description,
        }


@dataclass(kw_only=True)
class ProductCategorization:
    product_categorization_tier_1: str
    product_categorization_tier_2: str
    product_categorization_tier_3: str


@dataclass(kw_only=True)
class CreateIncidentInput(OperationalCategorization, ProductCategorization):
    action: str = "CREATE"
    assigned_support_company: str = "CENIT"
    assigned_support_organization: str = "Soporte Tecnico"
    company: str = "CENIT"
    direct_contact_first_name: str = "Integracion"
    direct_contact_last_name: str = "Datasmart"
    first_name: str = "Integracion"
    impact: str
    last_name: str = "Datasmart"
    manufacturer: str = "CENIT"
    reported_source: str = "Self Service"
    service_type: str = "User Service Request"
    status: str = "Assigned"
    urgency: str


@dataclass
class CreateIncidentInputZabbix:
    event_id: str
    impact: str
    operational_categorization_id: int
    product_categorization_id: int
    service_code: str
    title: str
    urgency: str

    def to_input_dict(self) -> dict:
        return {
            "impact": self.impact,
            "title": self.title,
            "urgency": self.urgency,
        }


@dataclass
class IncidentResponse:
    incident_number: str
    request_id: str


@dataclass
class IncidentInfo:
    assigned_group: str
    assignee: str
    categorization_tier_1: str
    categorization_tier_2: str
    categorization_tier_3: str
    description: str
    detailed_description: str
    incident_number: str
    impact: str
    priority: str
    product_categorization_tier_1: str
    product_categorization_tier_2: str
    product_categorization_tier_3: str
    product_name: str
    status: str
    submit_date: str
    urgency: str


@dataclass
class BmcHelixError:
    """Represents a single error object returned by the BMC Helix REST API."""

    message_type: str
    message_text: str
    message_number: int
    message_appended_text: str
