from __future__ import annotations

from typing import List, Optional, Dict, Any
from typing_extensions import Literal, Required, Annotated, TypedDict

from pydantic import Field

from .._utils import PropertyInfo
from .._models import BaseModel


# Instance相关类型定义 - 只读接口
class ListOndemandInstanceLimitReq(TypedDict, total=False):
    """列出按需实例限制请求"""
    region: Required[str]
    """区域"""
    cluster: Annotated[Optional[str], PropertyInfo(alias="cluster")]
    """集群"""
    tenant_name: Annotated[Optional[str], PropertyInfo(alias="tenantName")]
    """租户名称"""
    page: Annotated[Optional[int], PropertyInfo(alias="page", default=1)]
    """页码"""
    page_size: Annotated[Optional[int], PropertyInfo(alias="pageSize", default=10)]
    """页大小"""


class ConfigMapInstanceInfo(BaseModel):
    """配置映射实例信息"""
    showname: str
    """显示名称"""
    cpu: str
    """CPU"""
    memory: str
    """内存"""
    cost: Optional[str]
    """成本"""
    description: Optional[str]
    """描述"""
    ib: Optional[str]
    """IB"""
    gpu_type: Optional[str] = Field(alias="gpu-type")
    """GPU类型"""
    gpu_num: Optional[str] = Field(alias="gpu-num")
    """GPU数量"""


class ListInstanceQuotOrderItem(BaseModel):
    """列出实例配额订单项目"""
    id: int
    """ID"""
    order_id: str = Field(alias="orderId")
    """订单ID"""
    region: str
    """区域"""
    tenant_name: str = Field(alias="tenantName")
    """租户名称"""
    cluster: str
    """集群"""
    status: str
    """状态"""
    buy_at: str = Field(alias="buyAt")
    """购买时间"""
    expire_at: str = Field(alias="expireAt")
    """过期时间"""
    duration: int
    """持续时间"""
    buyer: str
    """购买者"""
    instance_type: str = Field(alias="instanceType")
    """实例类型"""
    instance_quantity: int = Field(alias="instanceQuantity")
    """实例数量"""


class ListOndemandInstanceLimitItem(BaseModel):
    """列出按需实例限制项目"""
    id: int
    """ID"""
    region: str
    """区域"""
    tenant_name: str = Field(alias="tenantName")
    """租户名称"""
    cluster: str
    """集群"""
    create_at: str = Field(alias="createAt")
    """创建时间"""
    update_at: str = Field(alias="updateAt")
    """更新时间"""
    creator: str
    """创建者"""
    instance_type: str = Field(alias="instanceType")
    """实例类型"""
    instance_quantity: int = Field(alias="instanceQuantity")
    """实例数量"""


class ListInstanceQuotaReq(TypedDict, total=False):
    """列出实例配额请求"""
    region: Annotated[Optional[str], PropertyInfo(alias="region")]
    """区域"""
    cluster: Annotated[Optional[str], PropertyInfo(alias="cluster")]
    """集群"""
    tenant_name: Annotated[Optional[str], PropertyInfo(alias="tenantName")]
    """租户名称"""
    resource_pool_qos_type: Annotated[Optional[str], PropertyInfo(alias="resourcePoolQosType")]
    """资源池QoS类型"""


class InstanceQuotaItem(BaseModel):
    """实例配额项目"""
    id: int
    """ID"""
    region: str
    """区域"""
    cluster: str
    """集群"""
    resource_pool_qos_type: str = Field(alias="resourcePoolQosType")
    """资源池QoS类型"""
    resource_pool_type: str = Field(alias="resourcePoolType")
    """资源池类型"""
    resource_pool_name: str = Field(alias="resourcePoolName")
    """资源池名称"""
    resource_pool_isolation: str = Field(alias="resourcePoolIsolation")
    """资源池隔离"""
    instance_name: str = Field(alias="instanceName")
    """实例名称"""
    quota: int
    """配额"""
    avail: int
    """可用"""
    used: int
    """已使用"""
    preempted: int
    """抢占"""
    authorized_users: List[str] = Field(alias="authorizedUsers")
    """授权用户"""
    creator: str
    """创建者"""
    created_at: str = Field(alias="createdAt")
    """创建时间"""
    expire_at: str = Field(alias="expireAt")
    """过期时间"""


class InstanceSummaryResponse(BaseModel):
    """实例摘要响应"""
    total_gpu: int = Field(alias="totalGpu")
    """总GPU"""
    used_gpu: int = Field(alias="usedGpu")
    """已使用GPU"""
    total_volume: int = Field(alias="totalVolume")
    """总Volume"""
    used_volume: int = Field(alias="usedVolume")
    """已使用Volume"""
    volume_unit: str = Field(alias="volumeUnit")
    """Volume单位"""


class UserInstanceUsageInfo(BaseModel):
    """用户实例使用信息"""
    user: str
    """用户"""
    usages: Dict[str, int]
    """使用情况"""


class ResourcePoolItem(BaseModel):
    """资源池项目"""
    resource_pool_name: str = Field(alias="resourcePoolName")
    """资源池名称"""
    resource_pool_qos_type: str = Field(alias="resourcePoolQosType")
    """资源池QoS类型"""
    resource_pool_type: str = Field(alias="resourcePoolType")
    """资源池类型"""
    instance_name: str = Field(alias="instanceName")
    """实例名称"""
    user_instance_usage: List[UserInstanceUsageInfo] = Field(alias="userInstanceUsage")
    """用户实例使用情况"""


class UserInstanceUsage(BaseModel):
    """用户实例使用情况"""
    user: str
    """用户"""
    reserved: Dict[str, Dict[str, int]]
    """预留"""
    ondemand: Optional[Dict[str, Dict[str, int]]]
    """按需""" 