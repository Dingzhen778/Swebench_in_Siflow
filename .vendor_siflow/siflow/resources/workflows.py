from __future__ import annotations

import json
from typing import TYPE_CHECKING, Optional, Dict, Any

import httpx

from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._utils import maybe_transform
from .._resource import SyncAPIResource
from .._base_client import make_request_options
from .._response import to_raw_response_wrapper
from ..types.workflow import (
    BasicResponse,
    CreateWorkflowInstanceDirectRequest,
    ListWorkflowInstancesResponse,
    WorkflowStepsStatusResponse,
    WorkflowStep,
)

if TYPE_CHECKING:
    from .._client import SiFlow


__all__ = ["WorkflowInstances", "WorkflowInstancesWithRawResponse"]


class WorkflowInstances(SyncAPIResource):
    with_raw_response: WorkflowInstancesWithRawResponse

    def __init__(self, client: SiFlow) -> None:
        super().__init__(client)
        self.with_raw_response = WorkflowInstancesWithRawResponse(self)

    def _prepare_workflow_request(self, request: CreateWorkflowInstanceDirectRequest | Dict[str, Any]) -> Dict[str, Any]:
        """准备工作流请求，将 sfjob 和 sfinfer 字段序列化为 spec 字符串"""
        if isinstance(request, CreateWorkflowInstanceDirectRequest):
            request_dict = request.model_dump(by_alias=True)
        else:
            request_dict = request.copy()
        
        # 处理 steps 中的 sfjob 和 sfinfer 字段
        if "steps" in request_dict:
            for step in request_dict["steps"]:
                if step.get("type") == "sfjob" and "sfjob" in step:
                    # 将 sfjob 对象序列化为 JSON 字符串
                    step["spec"] = json.dumps(step["sfjob"], ensure_ascii=False)
                    # 删除 sfjob 字段，因为服务端期望的是 spec 字符串
                    del step["sfjob"]
                elif step.get("type") == "sfinfer" and "sfinfer" in step:
                    # 将 sfinfer 对象序列化为 JSON 字符串
                    step["spec"] = json.dumps(step["sfinfer"], ensure_ascii=False)
                    # 删除 sfinfer 字段，因为服务端期望的是 spec 字符串
                    del step["sfinfer"]
        
        return request_dict

    def create_direct(
        self,
        *,
        request: CreateWorkflowInstanceDirectRequest | Dict[str, Any],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> BasicResponse:
        # 准备请求数据，处理 sfjob 序列化
        prepared_request = self._prepare_workflow_request(request)
        
        return self._post(
            "/workflow-service/v1/instances/direct",
            body=prepared_request,
            cast_to=BasicResponse,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 15,
        status: Optional[str] | None = None,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> ListWorkflowInstancesResponse:
        query: Query = {
            "page": str(page),
            "pageSize": str(page_size),
        }
        if status:
            query["status"] = status
        return self._get(
            "/workflow-service/v1/instances",
            cast_to=ListWorkflowInstancesResponse,
            options=make_request_options(
                query=query,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )

    def delete(
        self,
        *,
        id: int,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> BasicResponse:
        return self._delete(
            f"/workflow-service/v1/instances/{id}",
            cast_to=BasicResponse,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )

    def get_steps_status(
        self,
        *,
        id: int,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> WorkflowStepsStatusResponse:
        return self._get(
            f"/workflow-service/v1/instances/{id}/steps",
            cast_to=WorkflowStepsStatusResponse,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )


class WorkflowInstancesWithRawResponse:
    def __init__(self, resource: WorkflowInstances) -> None:
        self._resource = resource

    def create_direct(self, *args, **kwargs) -> httpx.Response:  # type: ignore[override]
        return to_raw_response_wrapper(self._resource.create_direct)(*args, **kwargs)

    def list(self, *args, **kwargs) -> httpx.Response:  # type: ignore[override]
        return to_raw_response_wrapper(self._resource.list)(*args, **kwargs)

    def delete(self, *args, **kwargs) -> httpx.Response:  # type: ignore[override]
        return to_raw_response_wrapper(self._resource.delete)(*args, **kwargs)

    def get_steps_status(self, *args, **kwargs) -> httpx.Response:  # type: ignore[override]
        return to_raw_response_wrapper(self._resource.get_steps_status)(*args, **kwargs) 