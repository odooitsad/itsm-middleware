from dataclasses import dataclass


@dataclass
class IncidentResponse:
    incident_number: str
    request_id: str
