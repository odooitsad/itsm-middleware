from typing import Protocol

from src.modules.bmc_helix.domain.entities import (
    CreateIncidentInput,
    IncidentInfo,
    IncidentResponse,
)


class BmcHelixPort(Protocol):
    async def stop(self) -> None: ...
    async def fetch_token(self) -> str: ...
    def build_request_payload(self, payload: CreateIncidentInput) -> dict: ...
    async def create_incident(
        self, payload: CreateIncidentInput
    ) -> IncidentResponse: ...
    async def get_incident(self, incident_number: str) -> IncidentInfo: ...
