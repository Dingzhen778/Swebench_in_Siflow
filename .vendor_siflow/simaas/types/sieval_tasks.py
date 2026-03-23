from __future__ import annotations

from typing import Any, Dict, List, Literal, TypedDict
from datetime import datetime

from .._models import BaseModel


# clients
class SiFlowTaskPod(BaseModel):
    name: str
    containers: List[str]


# models
class TaskModelArgs(BaseModel):
    api_base: str | None = None
    api_key: str | None = None
    max_retries: int = 3
    concurrency_limit: int = 128
    max_tokens: int = 8192
    temperature: float = 0.7
    timeout: float = 3600.0


class TaskModel(BaseModel):
    name: str | None = None
    api_base: str | None = None
    api_key: str | None = None
    args: TaskModelArgs


class TaskSandbox(BaseModel):
    url: str | None = None


class TaskRunnerConfig(BaseModel):
    concurrency_limits: Dict[Literal["preprocess", "infer", "postprocess", "feedback"], int] | None = None
    max_iterations: int = 3
    auto_resume: bool = True
    profile_io: bool = True
    profile_stages: bool = True


# schemas
class TaskModelArgsParam(TypedDict, total=False):
    api_base: str | None
    api_key: str | None
    max_retries: int
    concurrency_limit: int
    max_tokens: int
    temperature: float
    timeout: float


class TaskModelParam(TypedDict, total=False):
    name: str | None
    api_base: str | None
    api_key: str | None
    args: TaskModelArgsParam


class TaskSandboxParam(TypedDict, total=False):
    url: str | None


class TaskRunnerConfigParam(TypedDict, total=False):
    concurrency_limits: Dict[Literal["preprocess", "infer", "postprocess", "feedback"], int] | None
    max_iterations: int
    auto_resume: bool
    profile_io: bool
    profile_stages: bool


class TaskBatchDelete(BaseModel):
    ids: List[int]


class TaskBatchStop(BaseModel):
    ids: List[int]


class TaskBatchResubmit(BaseModel):
    ids: List[int]


class TaskRead(BaseModel):
    id: int
    name_prefix: str
    description: str | None = None

    base_model: TaskModel
    judge_model: TaskModel | None = None
    sandbox: TaskSandbox | None = None
    case_ids: List[int]
    runner_config: TaskRunnerConfig | None = None

    status: str
    status_msg: str | None = None

    created_at: datetime
    updated_at: datetime


class TaskReadSimple(BaseModel):
    id: int
    name_prefix: str
    description: str | None = None

    status: str
    status_msg: str | None = None

    created_at: datetime
    updated_at: datetime


class TaskPodsRead(BaseModel):
    pods: List[SiFlowTaskPod]


class TaskLogsRead(BaseModel):
    logs: str


class TaskReportBrief(BaseModel):
    task_name: str
    max_iteration: int
    case_id: int | None = None
    case_name: str | None = None
    dataset_id: int | None = None
    dataset_name: str | None = None


class TaskReportMetrics(BaseModel):
    task_name: str
    case_id: int | None = None
    case_name: str | None = None
    dataset_id: int | None = None
    dataset_name: str | None = None
    score: float = 0.0
    metrics: Dict[str, Any]


class TaskLabelReport(BaseModel):
    score: float
    cases: List[TaskReportMetrics]


class TaskReportSample(BaseModel):
    sample_id: int
    iteration: int
    stage: str
    preprocess_result: Any | None = None
    infer_result: Any | None = None
    postprocess_result: Any | None = None
    feedback_result: Any | None = None
