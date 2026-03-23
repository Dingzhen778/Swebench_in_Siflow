from __future__ import annotations

from typing import List, Optional, Dict, Any
from typing_extensions import Literal, Required, Annotated, TypedDict

from pydantic import Field

from .._utils import PropertyInfo
from .._models import BaseModel


# Volume相关类型定义 - 只读接口
class VolumeQuota(BaseModel):
    """存储配额信息"""
    fs_type: str = Field(alias="fsType")
    """文件系统类型"""
    avail: int
    """可用配额"""
    price: float
    """价格"""
    concurrency: str
    """并发数"""
    quantity_unit: str = Field(alias="quantityUnit")
    """数量单位"""


class VolumeQuotaDetail(BaseModel):
    """存储配额详情"""
    region: str
    """区域"""
    cluster: str
    """集群"""
    fs_type: str = Field(alias="fsType")
    """文件系统类型"""
    total_quota: str = Field(alias="totalQuota")
    """总配额"""
    used_quota: str = Field(alias="usedQuota")
    """已使用配额"""
    avail_quota: str = Field(alias="availQuota")
    """可用配额"""


class VolumeItem(BaseModel):
    """Volume项目"""
    id: int
    """Volume ID"""
    created_at: str = Field(alias="createdAt")
    """创建时间"""
    updated_at: str = Field(alias="updatedAt")
    """更新时间"""
    name: str
    """Volume名称"""
    region: str
    """区域"""
    cluster: str
    """集群"""
    org_name: str = Field(alias="orgName")
    """组织名称"""
    user_name: str = Field(alias="userName")
    """用户名"""
    creator: str
    """创建者"""
    namespace: str
    """命名空间"""
    pvc_name: str = Field(alias="pvcName")
    """PVC名称"""
    fs_type: str = Field(alias="fsType")
    """文件系统类型"""
    fs_id: str = Field(alias="fsId")
    """文件系统ID"""
    capacity: str
    """容量"""
    used: str
    """已使用"""
    status: str
    """状态"""
    authorized_users: Dict[str, "UserVolumePerm"] = Field(alias="authorizedUsers")
    """授权用户"""


class UserVolumePerm(BaseModel):
    """用户Volume权限"""
    read_only: bool = Field(alias="readOnly")
    """是否只读"""
    path: str = Field(alias="path")
    """挂载路径"""

class ListVolumesResp(BaseModel):
    """列出Volume响应"""
    status: bool
    """状态"""
    message: str = Field(alias="msg")
    """消息"""
    total: int
    """总数"""
    page: int
    """页码"""
    page_size: int = Field(alias="pageSize")
    """页大小"""
    data: List[VolumeItem]
    """数据"""
    request_id: Optional[str] = Field(alias="request_id")
    """请求ID"""
    trace_id: Optional[str] = Field(alias="trace_id")
    """跟踪ID"""


class VolumeIdName(BaseModel):
    """Volume ID和名称"""
    id: int
    """Volume ID"""
    name: str
    """Volume名称"""
    pvc: str
    """PVC名称"""
    read_only: bool = Field(alias="readOnly")
    """是否只读"""
    namespace: str
    """命名空间"""
    fs_id: str = Field(alias="fsId")
    """文件系统ID""" 