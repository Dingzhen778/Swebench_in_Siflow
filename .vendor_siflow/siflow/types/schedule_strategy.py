from __future__ import annotations

from typing import List, Optional
from typing_extensions import Literal, Required, Annotated, TypedDict

from pydantic import Field

from .._utils import PropertyInfo
from .._models import BaseModel


NodeScheduleStrategyScope = Literal["user", "tenant"]
NodeScheduleStrategyType = Literal["NodeIn", "NodeNotIn"]
NodeScheduleStrategyWorkloadType = Literal["task", "llm-service", "deployment", "vscs", "jupyter", "general-service",]


class NodeScheduleStrategyCreateParams(TypedDict, total=False):
    scope: Required[NodeScheduleStrategyScope]
    node_names: Required[Annotated[List[str], PropertyInfo(alias="nodeNames")]]
    type: NodeScheduleStrategyType
    workload_types: Required[
        Annotated[List[NodeScheduleStrategyWorkloadType], PropertyInfo(alias="workloadTypes")]
    ]
    expire_at: Required[Annotated[int, PropertyInfo(alias="expireAt")]]
    reason: Optional[str]
    source: Optional[str]


class NodeScheduleStrategyUpdateParams(TypedDict, total=False):
    id: Required[int]
    scope: Required[NodeScheduleStrategyScope]
    node_name: Annotated[Optional[str], PropertyInfo(alias="nodeName")]
    type: NodeScheduleStrategyType
    workload_types: Annotated[
        Optional[List[NodeScheduleStrategyWorkloadType]], PropertyInfo(alias="workloadTypes")
    ]
    expire_at: Required[Annotated[int, PropertyInfo(alias="expireAt")]]
    reason: Optional[str]
    source: Optional[str]


class NodeScheduleStrategyItem(BaseModel):
    id: int
    scope: str
    tenant: Optional[str] = None
    user: Optional[str] = None
    node_name: str = Field(alias="nodeName")
    type: str
    workload_types: List[NodeScheduleStrategyWorkloadType] = Field(alias="workloadTypes", default_factory=list)
    reason: Optional[str] = None
    source: Optional[str] = None
    expire_at: int = Field(alias="expireAt")
    enabled: bool
    created_at: Optional[int] = Field(alias="createdAt", default=None)
    updated_at: Optional[int] = Field(alias="updatedAt", default=None)


class NodeScheduleStrategyListResponse(BaseModel):
    status: bool
    message: Optional[str] = Field(alias="msg", default=None)
    request_id: Optional[str] = Field(alias="request_id", default=None)
    trace_id: Optional[str] = Field(alias="trace_id", default=None)
    total: int
    page: int
    page_size: int = Field(alias="pageSize")
    rows: List[NodeScheduleStrategyItem] = Field(default_factory=list)
