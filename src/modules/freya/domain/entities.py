from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from src.modules.freya.domain.exceptions import FreyaClientError


@dataclass
class AuthToken:
    access_token: str
    token_type: str = "Bearer"

    @property
    def authorization_header(self) -> str:
        """Return the formatted Authorization header value."""
        return f"{self.token_type} {self.access_token}"


@dataclass
class CreateIMInput:
    affected_ci: str
    area: str
    category: str
    ci_is_operational: bool
    description: list[str]
    event_id: str
    impact: str
    init_service: str
    origin: str
    sub_category: str
    title: str
    urgency: str


@dataclass
class UpdateIMInput:
    existing_im: str
    working_note: list[str]
    type: str


@dataclass
class CloseIMInput:
    im_id: str
    service_end_date: str


@dataclass
class IMResult:
    detail: str
    im: str | None = None


@dataclass
class FreyaResponse:
    code: str
    desc: str
    results: str | list[str] | dict[str, str]

    def __post_init__(self) -> None:
        if not isinstance(self.results, (str, dict, list)):
            raise FreyaClientError(
                "Unexpected 'results' type in Freya response: "
                f"{type(self.results).__name__}"
            )

    def has_an_error_code(self) -> bool:
        """
        Determine whether a response code returned by Freya indicates an error.

        Examples:
            >>> FreyaResponse("0", "OK", []).has_an_error_code()
            False
            >>> FreyaResponse("-1", "Error", []).has_an_error_code()
            True
            >>> FreyaResponse("0", "OK", []).has_an_error_code()
            False
            >>> FreyaResponse("-2", "Error", []).has_an_error_code()
            True
            >>> FreyaResponse("1", "OK", []).has_an_error_code()
            False
        """
        if isinstance(self.code, str):
            c = self.code.strip()
            if c.startswith("-") and c[1:].isdigit():
                return int(c) < 0

        if self.code is None:
            return False

        if isinstance(self.code, (int, float)):
            return int(self.code) < 0

        return False

    def get_result_text(self) -> str:
        if isinstance(self.results, list):
            return ", ".join(str(r) for r in self.results)
        if isinstance(self.results, dict):
            return self.results.get("results", str(self.results))
        return self.results


class TransactionStatus(str, Enum):
    PENDING = "En proceso"
    SUCCESS = "Procesado"
    ERROR = "Procesado con error"


class IMStatus(int, Enum):
    OPEN = 0
    CLOSED = 1
    ERROR = -1


@dataclass
class Transaction:
    service_code: str
    event_id: str
    request: dict
    status: TransactionStatus = TransactionStatus.PENDING
    status_im: IMStatus = IMStatus.ERROR
    im_id: str | None = None
    hostid: int | None = None
    response: dict | None = None
    id: int | None = None
    created_at: datetime | None = None
