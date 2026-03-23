from __future__ import annotations

from typing import List, Union, Optional, Dict
from typing_extensions import Literal, Required, Annotated, TypedDict

from pydantic import Field

from .._utils import PropertyInfo
from .._models import BaseModel


# entities
class TaskVolume(TypedDict, total=False):
    volume_id: Annotated[Optional[int], PropertyInfo(alias="volumeId")]
    """id of volume in db"""

    volume_name: Annotated[Optional[str], PropertyInfo(alias="volumeName")]
    """name of volume in db"""

    mount_dir: Annotated[str, PropertyInfo(alias="mountDir")]
    """the path of the volume mounted in task pod"""


class TaskDataset(BaseModel):
    name: str
    """dataset name"""

    version: Optional[str]
    """dataset version"""

    type: Optional[Literal["preset", "custom"]]
    """dataset type"""

    pvc_name: Optional[str] = Field(alias="pvc")
    """pvc name of dataset"""

    sub_path: Optional[str] = Field(alias="subPath")
    """relative path of dataset in volume"""

    mount_path: str = Field(alias="mountPath")
    """dataset mount path in task pod"""


class TaskModel(BaseModel):
    name: str
    """model name"""

    version: Optional[str]
    """model version"""

    type: Optional[Literal["preset", "custom"]]
    """model type"""

    pvc_name: Optional[str] = Field(alias="pvc")
    """pvc name of model"""

    sub_path: Optional[str] = Field(alias="subPath")
    """relative path of model in volume"""

    mount_path: str = Field(alias="mountPath")
    """model mount path in task pod"""


class TaskEnv(TypedDict, total=False):
    env_key: Annotated[Optional[str], PropertyInfo(alias="envKey")]
    """env key of model"""

    env_value: Annotated[Optional[str], PropertyInfo(alias="envValue")]
    """env value of model in volume"""

    hide: Annotated[Optional[bool], PropertyInfo(alias="hide")]
    """hide"""


class TaskUserSelectedInstance(TypedDict, total=False):
    name: str
    """instance name"""

    count_per_pod: Annotated[int, PropertyInfo(alias="countPerPod")]
    """instance number should used by one task pod"""


class TaskSystemSelectedInstance(BaseModel):
    name: str
    """instance name"""

    count_total: int = Field(alias="countTotal")
    """total instance number used by task"""


class TaskEnhancementsFaultTolerance(TypedDict, total=False):
    enabled: Optional[bool]
    """enable fault tolerance"""

    max_retry_count: Annotated[Optional[int], PropertyInfo(alias="maxRetryCount")]
    """max retry count when task error"""

    records: Annotated[Optional[List[str]], PropertyInfo(alias="records")]
    """records"""


class TaskDebugMode(TypedDict, total=False):
    enabled: Optional[bool]
    """enable debug mode"""

    holding: Optional[bool]
    """whether to hold the task pod after finish"""

    ttl: Optional[int]
    """hold time in seconds"""


class TaskEnhancements(TypedDict, total=False):
    fault_tolerance: Annotated[Optional[TaskEnhancementsFaultTolerance], PropertyInfo(alias="faultTolerance")]
    """fault tolerance config"""

    debug_mode: Annotated[Optional[TaskDebugMode], PropertyInfo(alias="debugMode")]
    """debug mode config"""


class TasksAheadBreakdown(TypedDict, total=False):
    high: Required[int]
    medium: Required[int]
    low: Required[int]


class TaskQueueInfo(TypedDict, total=False):
    rank_in_pool: Required[Annotated[int, PropertyInfo(alias="rankInPool")]]
    ahead_in_pool: Required[Annotated[TasksAheadBreakdown, PropertyInfo(alias="aheadInPool")]]
    rank_in_user: Required[Annotated[int, PropertyInfo(alias="rankInUser")]]
    ahead_in_user: Required[Annotated[TasksAheadBreakdown, PropertyInfo(alias="aheadInUser")]]


TaskPriority = Literal["high", "medium", "low"]


class TaskBrief(BaseModel):
    uuid: str
    """uuid of task"""

    cluster: str
    """cluster"""

    name: str
    """task name"""

    resource_pool: str = Field(alias="resourcePool")
    """instance resource pool"""

    instances: List[TaskUserSelectedInstance]
    """instances params when create task"""

    selected_instances: List[TaskSystemSelectedInstance] = Field(alias="selectedInstances")
    """selected instance"""

    volumes: List[TaskVolume]
    """volumes mounted by task"""

    image: str
    """image name"""

    image_version: str = Field(alias="imageVersion")
    """image version"""

    image_url: str = Field(alias="imageUrl")
    """image url"""

    image_type: str = Field(alias="imageType")
    """image type"""

    status: Union[
        str,
        Literal[
            "Pending", "Running", "Failed", "Succeeded", "Error", "PartialPending", "Unknown", "Stopping", "Stopped"
        ],
    ]
    """task status"""

    status_msg: str = Field(alias="statusMsg")
    """message of task status"""

    create_time: Optional[str] = Field(alias="createTime")
    """create time"""

    update_time: Optional[str] = Field(alias="updateTime")
    """update time"""

    start_time: Optional[str] = Field(alias="startTime")
    """start time"""

    end_time: Optional[str] = Field(alias="endTime")
    """end time"""

    duration: Optional[str] = Field(alias="duration")
    """duration"""

    priority: Optional[TaskPriority] = None
    """task priority"""

    guarantee: Optional[bool] = None
    """whether the task is guaranteed (non-preemptible)"""

    queue_info: Optional[TaskQueueInfo] = Field(alias="queueInfo", default=None)
    """task queue info"""

    task_env: List[TaskEnv] = Field(alias="taskEnv", default_factory=list)
    """task envs"""

    shared_users: List[str] = Field(alias="sharedUsers", default_factory=list)
    """shared users"""

    owner: Optional[str] = None
    """task owner"""

    enhancements: Optional[TaskEnhancements] = None
    """enhancements configs"""


class TaskOSS(BaseModel):
    bucket: Optional[str] = None
    path: Optional[str] = None
    endpoint: Optional[str] = None
    access_key: Optional[str] = Field(alias="accessKey", default=None)
    secret_key: Optional[str] = Field(alias="secretKey", default=None)
    region: Optional[str] = None


class Task(TaskBrief):
    name_prefix: str = Field(alias="namePrefix")
    """name prefix of task"""

    type: Literal["pytorchjob", "pod"]
    """task type"""

    workers: int
    """worker count of task"""

    cmd: str
    """command of task"""

    datasets: Optional[List[TaskDataset]] = None
    """datasets used by task"""

    models: Optional[List[TaskModel]] = None
    """models used by task"""

    product: Optional[str] = None
    """product line"""

    module: Optional[str] = None
    """module"""

    oss: Optional[TaskOSS] = None
    """oss config"""

    timezone: Optional[str] = None
    """timezone"""

    dashboard_url: Optional[str] = Field(alias="dashboardUrl", default=None)
    """dashboard url"""


class TaskPod(BaseModel):
    name: str
    """pod name"""

    status: str
    """pod status"""

    status_msg: Optional[str] = Field(alias="statusMsg", default=None)
    """pod status message"""

    node: Optional[str] = None
    """node name"""

    ip: Optional[str] = None
    """pod ip"""

    create_time: Optional[str] = Field(alias="createTime", default=None)
    """create time"""

    update_time: Optional[str] = Field(alias="updateTime", default=None)
    """update time"""

    containers: List[str] = Field(default_factory=list)
    """container names"""

    exit_code: Optional[int] = Field(alias="exitCode", default=None)
    """exit code"""

    deleted: Optional[bool] = None
    """whether the pod is marked as deleted"""

# requests
class TaskCreateParams(TypedDict, total=False):
    name_prefix: Required[Annotated[str, PropertyInfo(alias="namePrefix")]]
    """name prefix for task"""

    image: Required[str]
    """image name of task pod"""

    image_version: Required[Annotated[str, PropertyInfo(alias="imageVersion")]]
    """image version"""

    image_url: Required[Annotated[str, PropertyInfo(alias="imageUrl")]]
    """harbor url of image"""

    image_type: Annotated[Optional[Literal["preset", "custom"]], PropertyInfo(alias="imageType")]
    """image type"""

    type: Required[Annotated[Literal["pytorchjob", "pod"], PropertyInfo(alias="type")]]
    """task type"""

    workers: Required[int]
    """worker number of task"""

    volumes: List[TaskVolume]
    """volumes should mount by task"""

    datasets: List[TaskDataset]
    """datasets should used by task"""

    models: List[TaskModel]
    """models should used by task"""

    taskEnv: List[TaskEnv]
    """models should used by task"""

    resource_pool: Required[Annotated[str, PropertyInfo(alias="resourcePool")]]
    """instance resource pool name"""

    instances: Required[List[TaskUserSelectedInstance]]
    """instance types and numbers used by task"""

    priority: Optional[Literal["high", "medium", "low"]]
    """task priority"""

    guarantee: Optional[bool]
    """whether the task is guaranteed (non-preemptible)"""

    cmd: Required[str]
    """entrance command of task"""

    enhancements: Optional[TaskEnhancements]
    """enhancement configs"""

    product: Optional[str]
    """product line"""

    module: Optional[str]
    """module"""

    oss: Optional[TaskOSS]
    """oss config"""

    timezone: Optional[str]
    """timezone"""

    labels: Optional[Dict[str, str]]
    """labels"""


class TaskCreateResp(BaseModel):
    status: bool
    """response status"""

    msg: str
    """message of response status"""

    data: str
    """task uuid"""


class TaskDeleteResp(BaseModel):
    status: bool
    """response status"""

    msg: str
    """message of response status"""

    data: str
    """task uuid"""


class TaskBatchDeleteParams(TypedDict, total=False):
    uuids: Required[List[str]]
    """task uuids to delete"""


class TaskBatchDeleteResp(BaseModel):
    status: bool
    """response status"""

    msg: str
    """message of response status"""

    data: List[str]
    """task uuids"""


class TaskStopResp(BaseModel):
    status: bool
    """response status"""

    msg: str
    """message of response status"""

    data: str
    """task uuid"""


class TaskResubmitParams(TypedDict, total=False):
    uuids: Required[List[str]]
    """task uuids to resubmit"""


class TaskResubmitResp(BaseModel):
    status: bool
    """response status"""

    msg: str
    """message of response status"""

    data: List[str]
    """task uuids"""


class TaskBatchStopParams(TypedDict, total=False):
    uuids: Required[List[str]]
    """task uuids to stop"""


class TaskBatchStopResp(BaseModel):
    status: bool
    """response status"""

    msg: str
    """message of response status"""

    data: List[str]
    """task uuids"""
