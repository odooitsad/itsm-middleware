from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.clients.http import HttpResponse


class HttpClientError(Exception):
    """Raised by HttpxClient when an HTTP request fails (status error or connection error)."""

    def __init__(self, message: str, response: HttpResponse | None = None) -> None:
        super().__init__(message)
        self.response = response
