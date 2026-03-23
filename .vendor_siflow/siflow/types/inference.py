from __future__ import annotations

from typing import Optional, List, Dict, Any
from pydantic import Field, ConfigDict
from .._models import BaseModel

from .workflow import (
    LLMServiceConfig,
    LLMServingEngineConfig,
    LLMModelConfig,
    LLMWorkloadConfig,
    LLMMetricsConfig,
    LLMMonitoringConfig,
    LLMStorageConfig,
)


class ServiceStatus(BaseModel):
    """Service status information"""
    status: Optional[str] = None
    url_in_cluster: Optional[str] = Field(default=None, alias="urlInCluster")
    url_external: Optional[str] = Field(default=None, alias="urlExternal")
    current_version: Optional[int] = Field(default=None, alias="currentVersion")
    message: Optional[str] = None
    reason: Optional[str] = None


class Service(BaseModel):
    """Inference service definition"""
    model_config = ConfigDict(protected_namespaces=())
    
    id: Optional[int] = None
    created_at: Optional[str] = Field(default=None, alias="createdAt")
    updated_at: Optional[str] = Field(default=None, alias="updatedAt")
    deleted_at: Optional[str] = Field(default=None, alias="deletedAt")
    description: Optional[str] = None
    name: Optional[str] = None
    tenant: Optional[str] = None
    tenant_id: Optional[str] = Field(default=None, alias="tenantId")
    owner: Optional[str] = None
    status: Optional[ServiceStatus] = None
    resource_pool: Optional[str] = Field(default=None, alias="resourcePool")
    
    # Service configuration
    service_config: Optional[LLMServiceConfig] = Field(default=None, alias="serviceConfig")
    serving_engine_config: Optional[LLMServingEngineConfig] = Field(default=None, alias="servingEngineConfig")
    llm_model_config: Optional[LLMModelConfig] = Field(default=None, alias="modelConfig")
    workload_config: Optional[LLMWorkloadConfig] = Field(default=None, alias="workloadConfig")
    role_config: Optional[Dict[str, Any]] = Field(default=None, alias="roleConfig")
    metrics_config: Optional[LLMMetricsConfig] = Field(default=None, alias="metricsConfig")
    monitoring_config: Optional[LLMMonitoringConfig] = Field(default=None, alias="monitoringConfig")
    storage_config: Optional[LLMStorageConfig] = Field(default=None, alias="storageConfig")
    env: Optional[Dict[str, str]] = None


class ServiceBrief(BaseModel):
    """Brief service information for listing"""
    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    tenant: Optional[str] = None
    owner: Optional[str] = None
    status: Optional[ServiceStatus] = None
    resource_pool: Optional[str] = Field(default=None, alias="resourcePool")
    created_at: Optional[str] = Field(default=None, alias="createdAt")
    updated_at: Optional[str] = Field(default=None, alias="updatedAt")


class Instance(BaseModel):
    """Service instance information"""
    create_time: Optional[str] = Field(default=None, alias="createTime")
    name: Optional[str] = None
    status: Optional[str] = None
    pod_ip: Optional[str] = Field(default=None, alias="podIp")
    host_ip: Optional[str] = Field(default=None, alias="hostIp")
    hostname: Optional[str] = None
    message: Optional[str] = None
    reason: Optional[str] = None
    containers: Optional[List[str]] = None
    yaml: Optional[str] = None


class ListInstanceResponse(BaseModel):
    """Response for listing service instances"""
    rows: Optional[Dict[str, List[Instance]]] = None


class EngineVersion(BaseModel):
    """Engine version information"""
    id: Optional[int] = None
    engine_type: Optional[str] = Field(default=None, alias="engineType")
    engine_version: Optional[str] = Field(default=None, alias="engineVersion")
    image: Optional[str] = None
    created_at: Optional[str] = Field(default=None, alias="createdAt")


class EngineOption(BaseModel):
    """Engine option information"""
    engine_type: Optional[str] = Field(default=None, alias="engineType")
    engine_version: Optional[str] = Field(default=None, alias="engineVersion")
    execute_type: Optional[str] = Field(default=None, alias="executeType")


class StorageType(BaseModel):
    """Storage type information"""
    storage_type: Optional[str] = Field(default=None, alias="storageType")
    description: Optional[str] = None


class KVCacheOption(BaseModel):
    """KV cache option information"""
    kv_cache_type: Optional[str] = Field(default=None, alias="kvCacheType")
    description: Optional[str] = None


class ServiceStatusType(BaseModel):
    """Service status type information"""
    status: Optional[str] = None
    description: Optional[str] = None


class ServiceVersion(BaseModel):
    """Service version information"""
    version: Optional[int] = None
    created_at: Optional[str] = Field(default=None, alias="createdAt")
    updated_at: Optional[str] = Field(default=None, alias="updatedAt")
    status: Optional[str] = None


# Request/Response types
class ServiceCreateParams(BaseModel):
    """Parameters for creating a service"""
    model_config = ConfigDict(protected_namespaces=())
    
    description: Optional[str] = None
    name: Optional[str] = None
    tenant: Optional[str] = None
    tenant_id: Optional[str] = Field(default=None, alias="tenantId")
    owner: Optional[str] = None
    resource_pool: Optional[str] = Field(default=None, alias="resourcePool")
    
    # Service configuration
    service_config: Optional[LLMServiceConfig] = Field(default=None, alias="serviceConfig")
    serving_engine_config: Optional[LLMServingEngineConfig] = Field(default=None, alias="servingEngineConfig")
    llm_model_config: Optional[LLMModelConfig] = Field(default=None, alias="modelConfig")
    workload_config: Optional[LLMWorkloadConfig] = Field(default=None, alias="workloadConfig")
    role_config: Optional[Dict[str, Any]] = Field(default=None, alias="roleConfig")
    metrics_config: Optional[LLMMetricsConfig] = Field(default=None, alias="metricsConfig")
    monitoring_config: Optional[LLMMonitoringConfig] = Field(default=None, alias="monitoringConfig")
    storage_config: Optional[LLMStorageConfig] = Field(default=None, alias="storageConfig")
    env: Optional[Dict[str, str]] = None


class ServiceUpdateParams(ServiceCreateParams):
    """Parameters for updating a service"""
    pass


class ServiceScaleParams(BaseModel):
    """Parameters for scaling a service"""
    model_config = ConfigDict(protected_namespaces=())
    
    # Scale configuration - typically includes replicas for each role
    role_config: Optional[Dict[str, Any]] = Field(default=None, alias="roleConfig")


class ServiceListParams(BaseModel):
    """Parameters for listing services"""
    id: Optional[str] = None
    tenant: Optional[str] = None
    owner: Optional[str] = None
    status: Optional[str] = None
    name: Optional[str] = None
    page: Optional[int] = 1
    page_size: Optional[int] = Field(default=15, alias="pageSize")


class EngineVersionCreateParams(BaseModel):
    """Parameters for creating an engine version"""
    engine_type: Optional[str] = Field(default=None, alias="engineType")
    engine_version: Optional[str] = Field(default=None, alias="engineVersion")
    image: Optional[str] = None


# Response types
class ServiceCreateResp(BaseModel):
    """Response for creating a service"""
    data: Optional[int] = None  # Service ID


class ServiceUpdateResp(BaseModel):
    """Response for updating a service"""
    data: Optional[int] = None  # Service ID


class ServiceDeleteResp(BaseModel):
    """Response for deleting a service"""
    data: Optional[int] = None  # Service ID


class ServiceGetResp(BaseModel):
    """Response for getting a service"""
    data: Optional[Service] = None


class ServiceListResp(BaseModel):
    """Response for listing services"""
    rows: Optional[List[ServiceBrief]] = None
    total: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = Field(default=None, alias="pageSize")


class EngineVersionCreateResp(BaseModel):
    """Response for creating an engine version"""
    data: Optional[int] = None  # Engine version ID


class EngineVersionListResp(BaseModel):
    """Response for listing engine versions"""
    rows: Optional[List[EngineVersion]] = None
    total: Optional[int] = None


class EngineOptionsListResp(BaseModel):
    """Response for listing engine options"""
    rows: Optional[List[EngineOption]] = None


class StorageTypeListResp(BaseModel):
    """Response for listing storage types"""
    rows: Optional[List[StorageType]] = None


class KVCacheOptionsListResp(BaseModel):
    """Response for listing KV cache options"""
    rows: Optional[List[KVCacheOption]] = None


class ServiceStatusesListResp(BaseModel):
    """Response for listing service statuses"""
    rows: Optional[List[ServiceStatusType]] = None


class ServiceVersionsListResp(BaseModel):
    """Response for listing service versions"""
    rows: Optional[List[ServiceVersion]] = None
