# from typing import List, Optional
from .._models import BaseModel
from typing import List, Optional, Any
from datetime import datetime



# 基础结构
class Endpoints(BaseModel):
    internal: str
    external: str
    method: str


class Instance(BaseModel):
    name: str
    countPerPod: int


class Volume(BaseModel):
    volumeId: Optional[int] = None
    mountDir: Optional[str] = None


class Image(BaseModel):
    name: str = ""
    version: str = ""
    url: str = ""
    type: str = ""


class PodStatus(BaseModel):
    podName: Optional[str] = None
    containerNames: Optional[List[str]] = None
    statusPhase: str = ""
    createTime: Optional[datetime] = None
    updateTime: Optional[datetime] = None
    startTime: Optional[datetime] = None
    finishedTime: Optional[datetime] = None
    ready: bool = False
    reason: Optional[str] = None
    started: bool = False
    hostIP: str = ""
    podIP: str = ""
    nodeName: str = ""


class CronInfo(BaseModel):
    actionTime: Optional[str] = None
    enable: Optional[bool] = None


class CronPolicy(BaseModel):
    restartTime: Optional[CronInfo] = None
    onlineTime: Optional[CronInfo] = None
    offlineTime: Optional[CronInfo] = None


# Workload
class Workload(BaseModel):
    versionName: Optional[str] = None
    version: Optional[str] = None
    replicas: Optional[int] = None
    resourcePool: Optional[str] = None
    instances: Optional[List[Instance]] = None
    image: Optional[Image] = None
    volumes: Optional[List[Volume]] = None
    cmd: Optional[str] = None
    endpoints: Optional[Endpoints] = None


# General Service
class GeneralsvcDetail(BaseModel):
    uuid: str
    cluster: str
    name: str
    useBaseUrl: Optional[bool] = None
    ports: Optional[List[int]] = None
    workloads: Optional[List[Workload]] = None
    createTime: str = ""
    updateTime: str = ""


class GeneralsvcBrief(BaseModel):
    uuid: str
    name: str
    workloadNum: int
    ports: Optional[List[int]] = None
    cronPolicy: Optional[CronPolicy] = None
    status: str = ""
    statusMsg: str = ""
    isOnline: bool = False
    createTime: str = ""
    updateTime: str = ""


# Response 基础
class BasicResponse(BaseModel):
    status: bool
    msg: str
    requestID: Optional[str] = None
    traceID: Optional[str] = None
    data: Optional[Any] = None


class PagedResponse(BasicResponse):
    total: int = 0
    page: int = 0
    pageSize: int = 0
    rows: Optional[Any] = None


# Requests / Responses
class CreateGeneralsvcRequest(BaseModel):
    name: str
    ports: Optional[List[int]] = None
    workloads: Optional[List[Workload]] = None
    useBaseUrl: Optional[bool] = None


class CreateGeneralsvcResponse(BasicResponse):
    data: Optional[str] = None


class DeleteGeneralsvcRequest(BaseModel):
    generalsvcUUID: str


class DeleteGeneralsvcResponse(BasicResponse):
    data: Optional[str] = None


class ListGeneralsvcsRequest(BaseModel):
    status: Optional[str] = None
    name: Optional[str] = None
    generalsvcUUID: Optional[str] = None
    sortBy: Optional[str] = None


class ListGeneralsvcsResponse(PagedResponse):
    rows: Optional[List[GeneralsvcBrief]] = None


class ListDeploymentsRequest(BaseModel):
    generalSvcUUID: str


class DeploymentBrief(BaseModel):
    generalSvcUUID: str
    workloadName: str
    workloadStatus: str
    endpoints: Optional[Endpoints] = None
    image: str = ""
    cmd: str = ""
    instances: Optional[List[Instance]] = None
    workloadStatusMsg: str = ""
    workloadCreateTime: str = ""
    workloadUpdateTime: str = ""
    podStatus: Optional[List[PodStatus]] = None


class ListDeploymentsResponse(PagedResponse):
    rows: Optional[List[DeploymentBrief]] = None
