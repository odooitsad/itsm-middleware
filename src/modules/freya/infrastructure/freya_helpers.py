from typing import Any


def is_an_error_code(code: Any) -> bool:
    """
    Determine whether a response code returned by Freya indicates an error.

    Examples:
        >>> is_an_error_code(None)
        False
        >>> is_an_error_code(-1)
        True
        >>> is_an_error_code(0)
        False
        >>> is_an_error_code("-2")
        True
        >>> is_an_error_code("1")
        False
    """
    if code is None:
        return False

    if isinstance(code, (int, float)):
        return int(code) < 0

    if isinstance(code, str):
        c = code.strip()
        if c.startswith("-") and c[1:].isdigit():
            return int(c) < 0

    return False
