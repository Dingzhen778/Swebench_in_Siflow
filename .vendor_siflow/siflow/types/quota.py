from __future__ import annotations

from typing import List, Optional, Dict, Any
from typing_extensions import Literal, Required, Annotated, TypedDict

from pydantic import Field

from .._utils import PropertyInfo
from .._models import BaseModel


# 用户级二级quota管理API - 只读接口
class InstanceUserQuotaResp(BaseModel):
    """实例用户配额响应"""
    id: int
    """ID"""
    user_name: str = Field(alias="userName")
    """用户名"""
    instance_quota_id: int = Field(alias="instanceQuotaId")
    """实例配额ID"""
    total: int
    """总数"""
    used: int
    """已使用"""
    creator: str
    """创建者""" 