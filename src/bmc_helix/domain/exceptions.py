class DomainException(Exception):
    """Base domain exception."""


class IncidentCreationError(DomainException):
    """Raised when the external ITSM adapter fails to create an incident."""


class IncidentNotFoundError(DomainException):
    """Raised when no incident matches the given identifier."""
