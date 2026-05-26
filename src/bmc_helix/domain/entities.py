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
    incident_id: str | None = None
    request: dict | None = None
    response: dict | None = None
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class CreateIncidentInput:
    assigned_group: str
    assigned_support_company: str
    assigned_support_organization: str
    assignee: str
    categorization_tier_1: str
    categorization_tier_2: str
    categorization_tier_3: str
    description: str
    detailed_description: str
    impact: str
    manufacturer: str
    product_categorization_tier_1: str
    product_categorization_tier_2: str
    product_categorization_tier_3: str
    service_type: str
    urgency: str


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
