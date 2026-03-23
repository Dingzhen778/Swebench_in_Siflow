from __future__ import annotations

from pydantic import Field
from typing import Generic, Optional, List, Any

from .._types import ModelT
from .._models import GenericModel


class CommonResponse(GenericModel):
    """Resource-Server通用响应结构"""
    status: bool
    """响应状态"""
    message: Optional[str] = Field(alias="msg", default=None)
    """响应消息"""
    request_id: Optional[str] = Field(alias="requestID", default=None)
    """请求ID"""
    trace_id: Optional[str] = Field(alias="traceID", default=None)
    """跟踪ID"""
    data: Optional[Any] = None
    """响应数据"""


class MeteringResponse(GenericModel):
    """Resource-Server计量响应结构"""
    status: bool
    """响应状态"""
    error: Optional[str] = None
    """错误信息"""
    total: int
    """总数"""
    rows: List[Any]
    """数据行"""


class DataResp(GenericModel, Generic[ModelT]):
    status: bool
    """response status"""

    message: str = Field(alias="msg")
    """message of response status"""

    data: ModelT
    """actual data"""


class ListResp(GenericModel, Generic[ModelT]):
    status: bool
    """response status"""

    message: str = Field(alias="msg")
    """message of response status"""
    
    total: Optional[int]
    """total items"""
    
    rows: List[ModelT]
    """list of models"""


class DataListResp(GenericModel, Generic[ModelT]):
    status: bool
    """response status"""

    message: str = Field(alias="msg")
    """message of response status"""

    data: List[ModelT]
    """actual data"""
