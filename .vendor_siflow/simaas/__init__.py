from __future__ import annotations

from . import types
from ._types import NoneType, Transport, ProxiesTypes
from ._utils import file_from_path
from ._client import (
    SiMaas,
    Stream,
    Timeout,
    RequestOptions,
)
from .__main__ import start_proxy
from ._version import __title__, __version__
from ._exceptions import (
    APIError,
    SiMaaSError,
    ConflictError,
    NotFoundError,
    APIStatusError,
    RateLimitError,
    APITimeoutError,
    BadRequestError,
    APIConnectionError,
    AuthenticationError,
    InternalServerError,
    PermissionDeniedError,
    UnprocessableEntityError,
    APIResponseValidationError,
)
from ._utils._logs import setup_logging as _setup_logging

__all__ = [
    "types",
    "NoneType",
    "Transport",
    "ProxiesTypes",
    "file_from_path",
    "SiMaas",
    "Stream",
    "Timeout",
    "RequestOptions",
    "start_proxy",
    "__title__",
    "__version__",
    "APIError",
    "SiMaaSError",
    "APIStatusError",
    "APITimeoutError",
    "APIConnectionError",
    "APIResponseValidationError",
    "BadRequestError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "UnprocessableEntityError",
    "RateLimitError",
    "InternalServerError",
]

_setup_logging()
