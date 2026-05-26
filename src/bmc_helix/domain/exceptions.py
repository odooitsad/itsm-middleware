from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.bmc_helix.domain.entities import BmcHelixError


class DomainException(Exception):
    """Base domain exception."""


class IncidentCreationError(DomainException):
    """Raised when the external ITSM adapter fails to create an incident."""

    def __init__(
        self, message: str, bmc_errors: list[BmcHelixError] | None = None
    ) -> None:
        super().__init__(message)
        self.bmc_errors: list[BmcHelixError] = bmc_errors or []


class BmcHelixClientError(DomainException):
    """Raised for unhandled 4xx/5xx errors returned by the BMC Helix API."""

    def __init__(
        self,
        message: str,
        status_code: int,
        bmc_errors: list[BmcHelixError] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.bmc_errors: list[BmcHelixError] = bmc_errors or []
