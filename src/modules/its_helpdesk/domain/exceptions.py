class DomainException(Exception):
    """Base domain exception."""


class TicketCreationError(DomainException):
    """Raised when the ITS Helpdesk adapter fails to create a ticket."""


class ItsHelpdeskClientError(DomainException):
    """Raised for unhandled 4xx/5xx errors returned by the ITS Helpdesk API."""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code
