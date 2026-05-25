from dataclasses import dataclass
from enum import Enum


class TransactionStatus(str, Enum):
    PENDING = "En proceso"
    SUCCESS = "Procesado"
    ERROR = "Procesado con error"


@dataclass
class CreateIncidentInput:
    description: str
    detailed_description: str
    impact: str
    urgency: str
    service_type: str
    categorization_tier_1: str
    categorization_tier_2: str
    categorization_tier_3: str
    product_categorization_tier_1: str
    product_categorization_tier_2: str
    product_categorization_tier_3: str
    manufacturer: str
    assigned_support_company: str
    assigned_support_organization: str
    assigned_group: str
    assignee: str


@dataclass
class IncidentResponse:
    incident_number: str
    request_id: str
