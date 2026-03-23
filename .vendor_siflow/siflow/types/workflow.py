from __future__ import annotations

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict, Annotated

from pydantic import Field, ConfigDict, model_validator

from .._models import BaseModel
from .._utils import PropertyInfo


class GlobalParameter(BaseModel):
	name: str
	value: str


class CronConfig(BaseModel):
	schedule: str
	timezone: str
	concurrency_policy: str = Field(alias="concurrencyPolicy")
	starting_deadline_seconds: int = Field(alias="startingDeadlineSeconds")
	successful_jobs_history_limit: int = Field(alias="successfulJobsHistoryLimit")
	failed_jobs_history_limit: int = Field(alias="failedJobsHistoryLimit")


class DAGTask(BaseModel):
	name: str
	template: str
	depends: Optional[str] = None
	when: Optional[str] = None


class DAGConfig(BaseModel):
	tasks: List[DAGTask]


class EnvVar(BaseModel):
	name: str
	value: str


# SfJob 相关结构体定义
class FaultToleranceConfig(BaseModel):
	enabled: Optional[bool] = Field(default=None, alias="enabled")
	max_retry_count: Optional[int] = Field(default=None, alias="maxRetryCount")


class Enhancements(BaseModel):
	fault_tolerance: Optional[FaultToleranceConfig] = Field(default=None, alias="faultTolerance")


class OSSConfig(BaseModel):
	bucket: str
	path: str


class InstanceConfig(BaseModel):
	instance_name: str = Field(alias="instanceName")
	instance_quantity: int = Field(alias="instanceQuantity")


class VolumeConfig(BaseModel):
	volume_id: Optional[int] = Field(default=None, alias="volumeId")
	volume_name: Optional[str] = Field(default=None, alias="volumeName")
	mount_dir: str = Field(alias="mountDir")
	
	@model_validator(mode='after')
	def validate_volume_identifier(self):
		"""验证volumeId和volumeName至少有一个被提供"""
		if self.volume_id is None and self.volume_name is None:
			raise ValueError("volumeId和volumeName至少需要提供一个")
		return self


class DatasetConfig(BaseModel):
	name: str
	version: Optional[str] = None
	type: Optional[str] = None
	pvc: str
	sub_path: Optional[str] = Field(default=None, alias="subPath")
	mount_path: str = Field(alias="mountPath")


class ModelConfig(BaseModel):
	name: str
	version: Optional[str] = None
	type: Optional[str] = None
	pvc: str
	sub_path: Optional[str] = Field(default=None, alias="subPath")
	mount_path: str = Field(alias="mountPath")


class SfJobSpec(BaseModel):
	name_prefix: str = Field(alias="namePrefix")
	image: str
	image_version: str = Field(alias="imageVersion")
	image_url: str = Field(alias="imageUrl")
	image_type: str = Field(alias="imageType")
	type: str
	replicas: int
	priority: Optional[str] = None
	cmd: str
	enhancements: Optional[Enhancements] = None
	oss: Optional[OSSConfig] = None
	resource_pool: str = Field(alias="resourcePool")
	instances: List[InstanceConfig]
	volumes: Optional[List[VolumeConfig]] = None
	datasets: Optional[List[DatasetConfig]] = None
	models: Optional[List[ModelConfig]] = None
	node_not_in: Optional[List[str]] = Field(default=None, alias="nodeNotIn")
	node_in: Optional[List[str]] = Field(default=None, alias="nodeIn")


# SfInfer (Sfllm) 相关结构体定义
class LLMServicePort(BaseModel):
	name: Optional[str] = None
	port: Optional[int] = None


class LLMProbeConfig(BaseModel):
	probe_path: Optional[str] = Field(default=None, alias="probePath")
	probe_port: Optional[int] = Field(default=None, alias="probePort")


class LLMProbe(BaseModel):
	probe_type: Optional[str] = Field(default=None, alias="probeType")
	probe_config: Optional[LLMProbeConfig] = Field(default=None, alias="probeConfig")
	timeout: Optional[int] = None


class LLMIngressConfig(BaseModel):
	register_domain: Optional[str] = Field(default=None, alias="registerDomain")
	register_path: Optional[str] = Field(default=None, alias="registerPath")
	register_port: Optional[int] = Field(default=None, alias="registerPort")


class LLMRegisterConfig(BaseModel):
	register_type: Optional[str] = Field(default=None, alias="registerType")
	ingress: Optional[List[LLMIngressConfig]] = None
	served_model_name: Optional[str] = Field(default=None, alias="servedModelName")


class LLMAutoScaleConfig(BaseModel):
	auto_scale_type: Optional[str] = Field(default=None, alias="autoScaleType")


class LLMServiceConfig(BaseModel):
	service_port: Optional[LLMServicePort] = Field(default=None, alias="servicePort")
	readiness_probe: Optional[LLMProbe] = Field(default=None, alias="readinessProbe")
	liveness_probe: Optional[LLMProbe] = Field(default=None, alias="livenessProbe")
	register_config: Optional[LLMRegisterConfig] = Field(default=None, alias="registerConfig")
	auto_scale_config: Optional[LLMAutoScaleConfig] = Field(default=None, alias="autoScaleConfig")


class LLMKVCacheServerConfig(BaseModel):
	kv_cache_server_host: Optional[str] = Field(default=None, alias="kvCacheServerHost")
	kv_cache_server_port: Optional[int] = Field(default=None, alias="kvCacheServerPort")


class LLMKVCacheConfig(BaseModel):
	kv_cache_type: Optional[str] = Field(default=None, alias="kvCacheType")
	kv_cache_server_config: Optional[LLMKVCacheServerConfig] = Field(default=None, alias="kvCacheServerConfig")
	connector_name: Optional[str] = Field(default=None, alias="connectorName")


class LLMParam(BaseModel):
	key: Optional[str] = None
	value: Optional[str] = None


class LLMServingEngineConfig(BaseModel):
	model_config = ConfigDict(protected_namespaces=())
	engine_type: Optional[str] = Field(default=None, alias="engineType")
	engine_version: Optional[str] = Field(default=None, alias="engineVersion")
	execute_type: Optional[str] = Field(default=None, alias="executeType")
	kv_cache_config: Optional[LLMKVCacheConfig] = Field(default=None, alias="kvCacheConfig")
	engine_params: Optional[List[LLMParam]] = Field(default=None, alias="engineParams")


class LLMResourceConfig(BaseModel):
	instance_name: Optional[str] = Field(default=None, alias="instanceName")
	instance_quantity: Optional[int] = Field(default=None, alias="instanceQuantity")


class LLMRoleConfig(BaseModel):
	replicas: Optional[int] = None
	command: Optional[str] = None
	args: Optional[str] = None
	resource_config: Optional[LLMResourceConfig] = Field(default=None, alias="resourceConfig")
	image: Optional[str] = None
	labels: Optional[Dict[str, str]] = None
	annotations: Optional[Dict[str, str]] = None


class LLMWorkloadConfig(BaseModel):
	type: Optional[str] = None


class LLMHuggingFaceConfig(BaseModel):
	model: Optional[str] = None
	token: Optional[str] = None


class LLMModelRepoConfig(BaseModel):
	uuid: Optional[str] = None
	variant: Optional[str] = None
	name: Optional[str] = None
	version: Optional[str] = None
	pvc: Optional[LLMModelPVC] = None
	metadata: Optional[LLMModelMetadata] = None


class LLMModelPVC(BaseModel):
	name: Optional[str] = None
	path: Optional[str] = None


class LLMModelMetadata(BaseModel):
	arch: Optional[str] = None
	dtype: Optional[str] = None
	params: Optional[Dict[str, Any]] = None


class LLMPVCConfig(BaseModel):
	model_config = ConfigDict(protected_namespaces=())
	persistent_volume_claim_name: Optional[str] = Field(default=None, alias="persistentVolumeClaimName")
	model_path: Optional[str] = Field(default=None, alias="modelPath")
	mount_path: Optional[str] = Field(default=None, alias="mountPath")


class LLMHostPathConfig(BaseModel):
	model_config = ConfigDict(protected_namespaces=())
	path: Optional[str] = None
	mount_path: Optional[str] = Field(default=None, alias="mountPath")
	model_path: Optional[str] = Field(default=None, alias="modelPath")


class LLMOssConfig(BaseModel):
	model_config = ConfigDict(protected_namespaces=())
	endpoint: Optional[str] = None
	access_key: Optional[str] = Field(default=None, alias="accessKey")
	secret_key: Optional[str] = Field(default=None, alias="secretKey")
	bucket: Optional[str] = None
	region: Optional[str] = None
	model_path: Optional[str] = Field(default=None, alias="modelPath")
	enable_cache: Optional[bool] = Field(default=None, alias="enableCache")


class LLMVolumeConfig(BaseModel):
	model_config = ConfigDict(protected_namespaces=())
	volume_id: Optional[int] = Field(default=None, alias="volumeId")
	volume_name: Optional[str] = Field(default=None, alias="volumeName")
	mount_path: Optional[str] = Field(default=None, alias="mountPath")
	model_path: Optional[str] = Field(default=None, alias="modelPath")
	persistent_volume_claim_name: Optional[str] = Field(default=None, alias="persistentVolumeClaimName")


class LLMStorage(BaseModel):
	pvc: Optional[LLMPVCConfig] = None
	host_path: Optional[LLMHostPathConfig] = Field(default=None, alias="hostPath")
	oss: Optional[LLMOssConfig] = None
	volume: Optional[LLMVolumeConfig] = None
	hugging_face: Optional[LLMHuggingFaceConfig] = Field(default=None, alias="hf")
	model_repo: Optional[LLMModelRepoConfig] = Field(default=None, alias="modelRepo")


class LLMModelSource(BaseModel):
	storage_type: Optional[str] = Field(default=None, alias="storageType")
	storage: Optional[LLMStorage] = None


class LLMModelConfig(BaseModel):
	model_config = ConfigDict(protected_namespaces=())
	lora_adapter: Optional[Dict[str, LLMModelSource]] = Field(default=None, alias="loraAdapter")
	model_source: Optional[LLMModelSource] = Field(default=None, alias="modelSource")


class LLMMonitoringRule(BaseModel):
	metric_name: Optional[str] = Field(default=None, alias="metricName")
	metric_value: Optional[float] = Field(default=None, alias="metricValue")
	operator: Optional[str] = None
	threshold: Optional[float] = None
	duration: Optional[str] = None


class LLMEmailConfig(BaseModel):
	email_address: Optional[str] = Field(default=None, alias="emailAddress")


class LLMWebhookConfig(BaseModel):
	webhook_url: Optional[str] = Field(default=None, alias="webhookURL")


class LLMNotifyConfig(BaseModel):
	email_config: Optional[LLMEmailConfig] = Field(default=None, alias="emailConfig")
	webhook_config: Optional[LLMWebhookConfig] = Field(default=None, alias="webhookConfig")


class LLMNotify(BaseModel):
	notify_type: Optional[str] = Field(default=None, alias="notifyType")
	config: Optional[LLMNotifyConfig] = None
	content: Optional[str] = None


class LLMMonitoringConfig(BaseModel):
	rules: Optional[List[LLMMonitoringRule]] = None
	notify_config: Optional[List[LLMNotify]] = Field(default=None, alias="notifyConfig")


class LLMMetricsConfig(BaseModel):
	metrics_type: Optional[str] = Field(default=None, alias="metricsType")
	metrics_port: Optional[int] = Field(default=None, alias="metricsPort")
	metrics_path: Optional[str] = Field(default=None, alias="metricsPath")


class LLMVolume(BaseModel):
	volume_id: Optional[int] = Field(default=None, alias="volumeId")
	fs_id: Optional[str] = Field(default=None, alias="fsId")
	fs_type: Optional[str] = Field(default=None, alias="fsType")
	name: Optional[str] = None
	namespace: Optional[str] = None
	pvc: Optional[str] = None
	read_only: Optional[bool] = Field(default=None, alias="readOnly")
	mount_path: Optional[str] = Field(default=None, alias="mountPath")


class LLMStorageConfig(BaseModel):
	file_system_volumes: Optional[List[LLMVolume]] = Field(default=None, alias="fileSystemVolumes")


class SfInferSpec(BaseModel):
	model_config = ConfigDict(protected_namespaces=())
	description: Optional[str] = None
	name: Optional[str] = None
	name_prefix: Optional[str] = Field(default=None, alias="namePrefix")
	resource_pool: Optional[str] = Field(default=None, alias="resourcePool")
	service_config: Optional[LLMServiceConfig] = Field(default=None, alias="serviceConfig")
	serving_engine_config: Optional[LLMServingEngineConfig] = Field(default=None, alias="servingEngineConfig")
	model_configuration: Optional[LLMModelConfig] = Field(default=None, alias="modelConfig")
	workload_config: Optional[LLMWorkloadConfig] = Field(default=None, alias="workloadConfig")
	role_config: Optional[Dict[str, LLMRoleConfig]] = Field(default=None, alias="roleConfig")
	metrics_config: Optional[LLMMetricsConfig] = Field(default=None, alias="metricsConfig")
	monitoring_config: Optional[LLMMonitoringConfig] = Field(default=None, alias="monitoringConfig")
	storage_config: Optional[LLMStorageConfig] = Field(default=None, alias="storageConfig")
	env: Optional[Dict[str, str]] = None
	
	@model_validator(mode='after')
	def validate_name_or_name_prefix(self):
		"""验证name和namePrefix至少有一个被提供"""
		if self.name is None and self.name_prefix is None:
			raise ValueError("name和namePrefix至少需要提供一个")
		return self


class WorkflowStep(BaseModel):
	type: str
	name: str
	display_name: Optional[str] = Field(default=None, alias="displayName")
	labels: Dict[str, str]
	retries: int
	timeout_seconds: int = Field(alias="timeoutSeconds")
	env: List[EnvVar]
	# 直接透传 Argo 的结构
	inputs: Optional[Dict[str, Any]] = None
	outputs: Optional[Dict[str, Any]] = None
	daemoned: Optional[bool] = None
	# 如果 type 是 sfjob，则使用 sfjob 字段
	sfjob: Optional[SfJobSpec] = None
	# 如果 type 是 sfinfer，则使用 sfinfer 字段
	sfinfer: Optional[SfInferSpec] = None


class CreateWorkflowInstanceDirectRequest(BaseModel):
	workflow_name: str = Field(alias="workflowName")
	# 服务器会从 Header 中解析 tenant/user，这里保留可选字段以便兼容
	tenant: Optional[str] = None
	user: Optional[str] = None
	description: Optional[str] = None
	global_params: List[GlobalParameter] = Field(default_factory=list, alias="globalParams")
	dag: DAGConfig
	steps: List[WorkflowStep]
	cron: Optional[CronConfig] = None


class BasicResponse(BaseModel):
	status: bool
	msg: Optional[str] = Field(default=None, alias="msg")
	data: Optional[Dict[str, Any]] = None


class WorkflowInstanceRow(BaseModel):
	id: int
	name: str
	created_at: int = Field(alias="createdAt")
	status: str
	current_step: Optional[str] = Field(default=None, alias="currentStep")
	message: Optional[str] = None
	is_cron: Optional[bool] = Field(default=None, alias="isCron")


class ListWorkflowInstancesResponse(BaseModel):
	status: bool
	msg: str
	total: int
	page: int
	page_size: int = Field(alias="pageSize")
	rows: List[WorkflowInstanceRow]


class WorkflowStepStatus(BaseModel):
	name: str
	template: str
	depends: str
	when: str
	status: str
	message: str
	started_at: str = Field(alias="startedAt")
	finished_at: str = Field(alias="finishedAt")
	duration: str
	task_name: str = Field(alias="taskName")


class WorkflowStepsStatusResponse(BaseModel):
	status: bool
	msg: str
	data: Dict[str, List[WorkflowStepStatus]] 