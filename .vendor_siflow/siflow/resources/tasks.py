from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional
from typing_extensions import Literal

import yaml
import httpx
import json

from ..types import (
    Task,
    TaskPod,
    DataResp,
    ListResp,
    TaskBrief,
    TaskModel,
    TaskEnv,
    TaskVolume,
    TaskDataset,
    TaskStopResp,
    TaskCreateResp,
    TaskDeleteResp,
    TaskCreateParams,
    TaskEnhancements,
    TaskResubmitResp,
    TaskResubmitParams,
    TaskBatchDeleteResp,
    TaskBatchDeleteParams,
    TaskUserSelectedInstance,
    TaskBatchStopResp,
    TaskBatchStopParams,
    TaskOSS,
)
from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._utils import required_args, maybe_transform
from .._resource import SyncAPIResource
from .._response import to_raw_response_wrapper, APIResponse
from .._base_client import make_request_options
from .._constants import RAW_RESPONSE_HEADER

if TYPE_CHECKING:
    from .._client import SiFlow


__all__ = ["Tasks", "TasksWithRawResponse"]


class Tasks(SyncAPIResource):
    with_raw_response: TasksWithRawResponse

    def __init__(self, client: SiFlow) -> None:
        super().__init__(client)
        self.with_raw_response = TasksWithRawResponse(self)

    @required_args(
        ["yaml_file"],
        ["name_prefix", "image", "image_version", "image_url", "type", "cmd", "workers", "resource_pool", "instances"],
    )
    def create(
        self,
        *,
        yaml_file: Optional[str] | None = None,
        name_prefix: str | NotGiven = NOT_GIVEN,
        image: str | NotGiven = NOT_GIVEN,
        image_version: str | NotGiven = NOT_GIVEN,
        image_url: str | NotGiven = NOT_GIVEN,
        image_type: Optional[Literal["preset", "custom"]] | NotGiven = NOT_GIVEN,
        type: Literal["pytorchjob", "pod"] | NotGiven = NOT_GIVEN,
        priority: Literal["high", "medium", "low"] | NotGiven = NOT_GIVEN,
        guarantee: Optional[bool] | NotGiven = NOT_GIVEN,
        cmd: str | NotGiven = NOT_GIVEN,
        workers: int | NotGiven = NOT_GIVEN,
        resource_pool: str | NotGiven = NOT_GIVEN,
        instances: List[TaskUserSelectedInstance] | NotGiven = NOT_GIVEN,
        volumes: Optional[List[TaskVolume]] = [],
        datasets: Optional[List[TaskDataset]] = [],
        models: Optional[List[TaskModel]] = [],
        task_env: Optional[List[TaskEnv]] = [],
        enhancements: Optional[TaskEnhancements] | NotGiven = NOT_GIVEN,
        product: str | NotGiven = NOT_GIVEN,
        module: str | NotGiven = NOT_GIVEN,
        oss: Optional[TaskOSS] | NotGiven = NOT_GIVEN,
        timezone: str | NotGiven = NOT_GIVEN,
        labels: Optional[dict[str, str]] = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> str:
        if yaml_file is not None:
            with open(yaml_file, "r") as f:
                params = yaml.safe_load(f)
            if "namePrefix" not in params:
                raise ValueError("missing 'namePrefix' in yaml file")
            if "image" not in params:
                raise ValueError("missing 'image' in yaml file")
            if "imageVersion" not in params:
                raise ValueError("missing 'imageVersion' in yaml file")
            if "imageUrl" not in params:
                raise ValueError("missing 'imageUrl' in yaml file")
            if "type" not in params:
                raise ValueError("missing 'type' in yaml file")
            if "cmd" not in params:
                raise ValueError("missing 'cmd' in yaml file")
            if "workers" not in params:
                raise ValueError("missing 'workers' in yaml file")
            if "resourcePool" not in params:
                raise ValueError("missing 'resourcePool' in yaml file")
            if "instances" not in params:
                raise ValueError("missing 'instances' in yaml file")
            if "priority" not in params:
                params["priority"] = "medium"
            if "guarantee" not in params:
                params["guarantee"] = None
            if "volumes" not in params:
                params["volumes"] = []
            if "datasets" not in params:
                params["datasets"] = []
            if "models" not in params:
                params["models"] = []
            if "taskEnv" not in params:
                params["taskEnv"] = []
            # handle new params in yaml if they exist
            if "product" not in params:
                params["product"] = None
            if "module" not in params:
                params["module"] = None
            if "oss" not in params:
                params["oss"] = None
            if "timezone" not in params:
                params["timezone"] = None
        else:
            params = {
                "namePrefix": name_prefix,
                "image": image,
                "imageVersion": image_version,
                "imageUrl": image_url,
                "imageType": image_type,
                "type": type,
                "workers": workers,
                "volumes": volumes,
                "datasets": datasets,
                "models": models,
                "taskEnv": task_env,
                "resourcePool": resource_pool,
                "instances": instances,
                "priority": priority,
                "guarantee": guarantee,
                "cmd": cmd,
                "enhancements": enhancements,
                "product": product,
                "module": module,
                "oss": oss,
                "timezone": timezone,
                "labels": labels,
            }
        
        # Validate volumes: each volume must have either volume_id or volume_name
        if "volumes" in params and params["volumes"]:
            for i, volume in enumerate(params["volumes"]):
                has_volume_id = volume.get("volumeId") is not None or volume.get("volume_id") is not None
                has_volume_name = volume.get("volumeName") is not None or volume.get("volume_name") is not None
                
                if not has_volume_id and not has_volume_name:
                    raise ValueError(f"Volume at index {i} must have either 'volumeId' or 'volumeName'")

        headers = extra_headers.copy() if extra_headers else {}
        if labels:
            try:
                labels_json = json.dumps(labels, ensure_ascii=False)
                headers["X-Labels"] = labels_json
            except Exception as e:
                raise ValueError(f"Failed to serialize labels to JSON: {e}")

        resp = self._post(
            "/task-service/v1/tasks",
            body=maybe_transform(params, TaskCreateParams),
            options=make_request_options(
                extra_headers=headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TaskCreateResp,
        )
        return resp.data

    @required_args(["uuid"])
    def delete(
        self,
        *,
        uuid: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> str:
        resp = self._delete(
            f"/task-service/v1/tasks/{uuid}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TaskDeleteResp,
        )
        return resp.data

    @required_args(["uuids"])
    def batch_delete(
        self,
        *,
        uuids: List[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> List[str]:
        params = {
            "uuids": uuids,
        }
        resp = self._post(
            "/task-service/v1/tasks/deletion",
            body=maybe_transform(params, TaskBatchDeleteParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TaskBatchDeleteResp,
        )
        return resp.data

    @required_args(["uuids"])
    def batch_stop(
        self,
        *,
        uuids: List[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> List[str]:
        params = {
            "uuids": uuids,
        }
        resp = self._post(
            "/task-service/v1/tasks/stop",
            body=maybe_transform(params, TaskBatchStopParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TaskBatchStopResp,
        )
        return resp.data

    @required_args(["uuid"])
    def stop(
        self,
        *,
        uuid: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> str:
        resp = self._get(
            f"/task-service/v1/tasks/stop/{uuid}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TaskStopResp,
        )
        return resp.data

    @required_args(["uuid"])
    def get(
        self,
        *,
        uuid: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> Task:
        resp = self._get(
            f"/task-service/v1/tasks/{uuid}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DataResp[Task],
        )
        return resp.data

    @required_args(["uuid"])
    def list_pods(
        self,
        *,
        uuid: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> List[TaskPod]:
        resp = self._get(
            f"/task-service/v1/tasks/{uuid}/pods",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DataResp[List[TaskPod]],
        )
        return resp.data

    def list(
        self,
        *,
        count: int = 15,
        status: str | None = None,
        priority: str | None = None,
        name: str | None = None,
        product: str | None = None,
        module: str | None = None,
        labels: str | None = None,
        is_share: bool | None = None,
        resource_pools: List[str] | None = None,
        is_task_admin: bool | None = None,
        owners: str | None = None,
        order_by: str | None = None,
        asc: bool | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> List[TaskBrief]:
        query: Query = {
            "page": "1",
            "pageSize": str(count),
        }
        if status is not None:
            query["status"] = status
        if priority is not None:
            query["priority"] = priority
        if name is not None:
            query["name"] = name
        if product is not None:
            query["product"] = product
        if module is not None:
            query["module"] = module
        if labels is not None:
            query["labels"] = labels
        if is_share is not None:
            query["isShare"] = str(is_share).lower()
        if resource_pools is not None:
            query["resourcePools"] = resource_pools
        if is_task_admin is not None:
            query["isTaskAdmin"] = str(is_task_admin).lower()
        if owners is not None:
            query["owners"] = owners
        if order_by is not None:
            query["orderBy"] = order_by
        if asc is not None:
            query["asc"] = str(asc).lower()

        resp = self._get(
            "/task-service/v1/tasks",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=query,
            ),
            cast_to=ListResp[TaskBrief],
        )
        return resp.rows

    @required_args(["uuids"])
    def resubmit(
        self,
        *,
        uuids: List[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> List[str]:
        params = {
            "uuids": uuids,
        }
        resp = self._post(
            "/task-service/v1/tasks/resubmission",
            body=maybe_transform(params, TaskResubmitParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TaskResubmitResp,
        )
        return resp.data


class TasksWithRawResponse:
    def __init__(self, tasks: Tasks) -> None:
        self.create = to_raw_response_wrapper(tasks.create)
        self.delete = to_raw_response_wrapper(tasks.delete)
        self.batch_delete = to_raw_response_wrapper(tasks.batch_delete)
        self.stop = to_raw_response_wrapper(tasks.stop)
        self.get = to_raw_response_wrapper(tasks.get)
        self.list_pods = to_raw_response_wrapper(tasks.list_pods)
        self.list = to_raw_response_wrapper(tasks.list)
        self.resubmit = to_raw_response_wrapper(tasks.resubmit)
        self.batch_stop = to_raw_response_wrapper(tasks.batch_stop)
