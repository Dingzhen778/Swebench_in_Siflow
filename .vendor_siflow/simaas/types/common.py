from __future__ import annotations

from typing import List, Generic, Optional

from pydantic import Field

from .._types import _T
from .._models import GenericModel


class DataResp(GenericModel, Generic[_T]):
    status: bool
    """response status"""

    message: str = Field(alias="msg")
    """message of response status"""

    data: _T
    """actual data"""


class ListResp(GenericModel, Generic[_T]):
    status: bool
    """response status"""

    message: str = Field(alias="msg")
    """message of response status"""

    total: Optional[int]
    """total items"""

    rows: List[_T]
    """list of models"""


class DataListResp(GenericModel, Generic[_T]):
    status: bool
    """response status"""

    message: str = Field(alias="msg")
    """message of response status"""

    data: List[_T]
    """actual data"""
