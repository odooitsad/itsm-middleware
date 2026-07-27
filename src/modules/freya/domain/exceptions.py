class DomainException(Exception):
    """Base domain exception for the Freya module."""


class FreyaAuthError(DomainException):
    """Raised when authentication against the Freya API fails."""

    def __init__(self, message: str = "Freya authentication error") -> None:
        super().__init__(message)


class FreyaClientError(DomainException):
    """Raised when a request to the Freya API fails or returns an error code."""

    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code
