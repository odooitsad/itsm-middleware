from typing import Protocol

from src.bmc_helix.domain.entities import CreateIncidentInput, IncidentResponse


class BmcHelixPort(Protocol):
    async def stop(self) -> None: ...
    async def fetch_token(self) -> str: ...
    async def create_incident(
        self, payload: CreateIncidentInput
    ) -> IncidentResponse: ...
