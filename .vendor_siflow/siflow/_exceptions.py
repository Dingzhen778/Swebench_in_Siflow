from __future__ import annotations

from typing import Any, Optional, cast
from typing_extensions import Literal

import httpx

from ._utils import is_dict

__all__ = [
    "BadRequestError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "UnprocessableEntityError",
    "RateLimitError",
    "InternalServerError",
]


class SiFlowError(Exception):
    pass


class APIError(SiFlowError):
    message: str
    request: httpx.Request

    body: object | None
    """The API response body.

    If the API responded with a valid JSON structure then this property will be the
    decoded result.

    If it isn't a valid JSON structure then this will be the raw response.

    If there was no response associated with this error then it will be `None`.
    """

    trace_id: Optional[str]=None
    request_id: Optional[str]=None

    def __init__(self, message: str, request: httpx.Request, *, body: object | None) -> None:
        super().__init__(message)
        self.request = request
        self.message = message
        
        if is_dict(body) and "traceID" in body:
            self.trace_id = cast(Any, body.get("traceID"))
        if is_dict(body) and "trace_id" in body:
            self.trace_id = cast(Any, body.get("trace_id"))
        if is_dict(body) and "requestID" in body:
            self.request_id = cast(Any, body.get("requestID"))
        if is_dict(body) and "request_id" in body:
            self.request_id = cast(Any, body.get("request_id"))


class APIResponseValidationError(APIError):
    response: httpx.Response
    status_code: int

    def __init__(self, response: httpx.Response, body: object | None, *, message: str | None = None) -> None:
        super().__init__(message or "Data returned by API invalid for expected schema.", response.request, body=body)
        self.response = response
        self.status_code = response.status_code


class APIStatusError(APIError):
    """Raised when an API response has a status code of 4xx or 5xx."""

    response: httpx.Response
    status_code: int

    def __init__(self, message: str, *, response: httpx.Response, body: object | None) -> None:
        super().__init__(message, response.request, body=body)
        self.response = response
        self.status_code = response.status_code


class APIConnectionError(APIError):
    def __init__(self, *, message: str = "Connection error.", request: httpx.Request, cause: Optional[Exception] = None) -> None:
        if cause and message == "Connection error.":
            # Include the original error message for better debugging
            # Try to get the most detailed error message, including underlying exceptions
            error_detail = str(cause)
            
            # Check for specific error types and provide helpful context
            underlying_error = None
            if hasattr(cause, '__cause__') and cause.__cause__:
                underlying_error = cause.__cause__
            
            # Check if it's an OSError with error code 99 (port exhaustion)
            os_error = None
            if isinstance(cause, OSError):
                os_error = cause
            elif underlying_error and isinstance(underlying_error, OSError):
                os_error = underlying_error
            
            if os_error and hasattr(os_error, 'errno') and os_error.errno == 99:
                error_detail = f"{error_detail}. This usually indicates client-side port exhaustion. Possible causes: too many connections created without closing, TIME_WAIT connections accumulating, or ephemeral port range exhausted. Consider reusing HTTP clients or increasing system port range."
            
            # If the exception has a __cause__ attribute, include it for more context
            # This helps with cases like port exhaustion, connection refused, etc.
            if underlying_error:
                underlying_error_str = str(underlying_error)
                if underlying_error_str and underlying_error_str not in error_detail:
                    error_detail = f"{error_detail} ({underlying_error_str})"
            
            error_msg = f"Connection error: {error_detail}"
        else:
            error_msg = message
        super().__init__(error_msg, request, body=None)
        self.cause = cause


class APITimeoutError(APIConnectionError):
    def __init__(self, request: httpx.Request) -> None:
        super().__init__(message="Request timed out.", request=request)


class BadRequestError(APIStatusError):
    status_code: Literal[400] = 400  # pyright: ignore[reportIncompatibleVariableOverride]


class AuthenticationError(APIStatusError):
    status_code: Literal[401] = 401  # pyright: ignore[reportIncompatibleVariableOverride]


class PermissionDeniedError(APIStatusError):
    status_code: Literal[403] = 403  # pyright: ignore[reportIncompatibleVariableOverride]


class NotFoundError(APIStatusError):
    status_code: Literal[404] = 404  # pyright: ignore[reportIncompatibleVariableOverride]


class ConflictError(APIStatusError):
    status_code: Literal[409] = 409  # pyright: ignore[reportIncompatibleVariableOverride]


class UnprocessableEntityError(APIStatusError):
    status_code: Literal[422] = 422  # pyright: ignore[reportIncompatibleVariableOverride]


class RateLimitError(APIStatusError):
    status_code: Literal[429] = 429  # pyright: ignore[reportIncompatibleVariableOverride]


class InternalServerError(APIStatusError):
    pass
