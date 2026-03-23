from __future__ import annotations
from .._models import BaseModel
from typing import  List, Optional, Dict, Any



# === 基础结构 ===


class UserSelectedInstance(BaseModel):
    name: str
    countPerPod: int



class SystemSelectedInstance(BaseModel):
    name: str
    countTotal: int



class ModelBrief(BaseModel):
    uuid: str
    variant: str
    name: str
    version: str



class Image(BaseModel):
    name: str
    version: str
    url: str
    type: str



class EndpointsBrief(BaseModel):
    internal: str
    external: str



class Endpoints(BaseModel):
    internal: str
    external: str
    example: str


# === 模型引用（通常来自 models 包） ===
# 这里只定义占位结构，你可以在实际项目中替换成真实定义。

class Volume(BaseModel):
    volumeId: Optional[int] = None
    mountDir: Optional[str] = None



class OSS(BaseModel):
    bucket: str
    path: str



class ModelPVC(BaseModel):
    name: str
    path: str



class ModelParams(BaseModel):
    value: float
    unit: str



class ModelMetric(BaseModel):
    metric: str
    value: float



class ModelMetadata(BaseModel):
    arch: Optional[str] = None
    dtype: Optional[str] = None
    params: Optional[ModelParams] = None
    metrics: Optional[List[ModelMetric]] = None



class Model(BaseModel):
    uuid: str
    variant: str
    name: str
    version: str
    pvc: ModelPVC
    mountPath: Optional[str] = None
    metadata: Optional[ModelMetadata] = None




# === CreateDeploymentRequest 主结构 ===


class CreateDeploymentRequest(BaseModel):
    product: Optional[str]                # models.InferProduct
    name: str
    version: str
    model: Optional[Model]                  # models.Model
    backend: str                          # models.InferBackend
    backendVersion: Optional[str]
    replicas: Optional[int]
    nodes: int
    resourcePool: str
    instances: List[UserSelectedInstance]
    image: Optional[Image]
    volumes: Optional[List[Volume]]
    cmd: Optional[str]
    preStopCmd: Optional[str]
    workerCmd: Optional[str]
    port: Optional[int]
    oss: Optional[OSS]
    metadata: Optional[ModelMetadata]

class UpdateDeploymentRequest(BaseModel):
    uuid: str            
    name: str
    version: str
    model: Optional[Model]                  # models.Model
    backend: str                          # models.InferBackend
    backendVersion: Optional[str]
    replicas: Optional[int]
    nodes: int
    resourcePool: str
    instances: List[UserSelectedInstance]
    image: Optional[Image]
    volumes: Optional[List[Volume]]
    cmd: Optional[str]
    preStopCmd: Optional[str]
    workerCmd: Optional[str]
    port: Optional[int]
    oss: Optional[OSS]
    metadata: Optional[ModelMetadata]


class DeploymentInfo(BaseModel):
    """部署信息"""
    uuid: str
    name: str
    model_uuid: str
    model_name: str
    model_version: str
    status: str
    replicas: int
    ready_replicas: int
    available_replicas: int
    cpu_request: str
    cpu_limit: str
    memory_request: str
    memory_limit: str
    gpu_request: int
    gpu_limit: int
    backend: str
    backend_version: str
    created_at: str
    updated_at: str
    description: str
    auto_scaling: bool
    env_vars: Dict[str, str]
    labels: Dict[str, str]
    annotations: Dict[str, str]

class ListDeploymentsResponse(BaseModel):
    """列表部署响应"""
    rows: Optional[List[DeploymentInfo]] = None

class PodInfo(BaseModel):
    """Pod信息"""
    name: str
    namespace: str
    status: str
    node_name: str
    pod_ip: str
    created_at: str
    ready: bool
    restart_count: int
    containers: List[Dict[str, Any]]


__all__ = [
    "CreateDeploymentRequest",
    "UpdateDeploymentRequest", 
    "DeploymentInfo",
    "PodInfo"
]

