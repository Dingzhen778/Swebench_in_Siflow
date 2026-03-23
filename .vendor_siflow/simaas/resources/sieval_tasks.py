from __future__ import annotations

import json
from typing import TYPE_CHECKING, Dict, List, Literal

import yaml
import httpx

from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._utils import required_args
from .._resource import SyncAPIResource
from .._response import to_raw_response_wrapper
from .._base_client import make_request_options
from ..types.common import DataResp, ListResp
from ..types.sieval_tasks import (
    TaskRead,
    TaskLogsRead,
    TaskPodsRead,
    TaskModelParam,
    TaskReadSimple,
    TaskLabelReport,
    TaskReportBrief,
    TaskReportSample,
    TaskSandboxParam,
    TaskRunnerConfigParam,
)

if TYPE_CHECKING:
    from .._client import SiMaas


class SiEvalTasks(SyncAPIResource):
    with_raw_response: SiEvalTasksWithRawResponse

    def __init__(self, client: SiMaas) -> None:
        super().__init__(client)
        self.with_raw_response = SiEvalTasksWithRawResponse(self)

    @required_args(["name_prefix", "yaml_file"], ["name_prefix", "base_model"])
    def create(
        self,
        name_prefix: str,
        description: str | None = None,
        *,
        yaml_file: str | None = None,
        base_model: TaskModelParam | None = None,
        judge_model: TaskModelParam | None = None,
        sandbox: TaskSandboxParam | None = None,
        case_ids: List[int] | None = None,
        runner_config: TaskRunnerConfigParam | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> int:
        if yaml_file is not None:
            with open(yaml_file, "r") as f:
                sieval_core_yaml = yaml.safe_load(f)
                resp = self._post(
                    "/sieval/v1/tasks/yaml",
                    body={
                        "name_prefix": name_prefix,
                        "description": description,
                        "raw_yaml": json.dumps(sieval_core_yaml),
                    },
                    options=make_request_options(
                        extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                    ),
                    cast_to=DataResp[int],
                )
        else:
            resp = self._post(
                "/sieval/v1/tasks",
                body={
                    "name_prefix": name_prefix,
                    "base_model": base_model,
                    "description": description,
                    "judge_model": judge_model,
                    "sandbox": sandbox,
                    "case_ids": case_ids,
                    "runner_config": runner_config,
                },
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=DataResp[int],
            )
        return resp.data

    @required_args(["id"])
    def resubmit(
        self,
        *,
        id: int,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> int:
        resp = self._post(
            f"/sieval/v1/tasks/{id}/resubmit",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DataResp[int],
        )
        return resp.data

    @required_args(["ids"])
    def batch_resubmit(
        self,
        *,
        ids: List[int],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> int:
        resp = self._post(
            "/sieval/v1/tasks/batch/resubmit",
            body={"ids": ids},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DataResp[int],
        )
        return resp.data

    @required_args(["id"])
    def delete(
        self,
        *,
        id: int,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> int:
        resp = self._delete(
            f"/sieval/v1/tasks/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DataResp[int],
        )
        return resp.data

    @required_args(["ids"])
    def batch_delete(
        self,
        *,
        ids: List[int],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> int:
        resp = self._post(
            "/sieval/v1/tasks/batch/delete",
            body={"ids": ids},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DataResp[int],
        )
        return resp.data

    @required_args(["id"])
    def stop(
        self,
        *,
        id: int,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> int:
        resp = self._post(
            f"/sieval/v1/tasks/{id}/stop",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DataResp[int],
        )
        return resp.data

    @required_args(["ids"])
    def batch_stop(
        self,
        *,
        ids: List[int],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> int:
        resp = self._post(
            "/sieval/v1/tasks/batch/stop",
            body={"ids": ids},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DataResp[int],
        )
        return resp.data

    @required_args(["id"])
    def get(
        self,
        *,
        id: int,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> TaskRead:
        resp = self._get(
            f"/sieval/v1/tasks/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DataResp[TaskRead],
        )
        return resp.data

    def list(
        self,
        *,
        count: int = 15,
        name: str | None = None,
        status: Literal["Pending", "Running", "Succeeded", "Failed"] | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> List[TaskReadSimple]:
        query: Query = {
            "page": "1",
            "page_size": str(count),
        }
        if name is not None:
            query["name"] = name
        if status is not None:
            query["status"] = status
        resp = self._get(
            "/sieval/v1/tasks",
            options=make_request_options(
                query=query,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=ListResp[TaskReadSimple],
        )
        return resp.rows

    @required_args(["id"])
    def get_pods(
        self,
        *,
        id: int,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> TaskPodsRead:
        resp = self._get(
            f"/sieval/v1/tasks/{id}/pods",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DataResp[TaskPodsRead],
        )
        return resp.data

    @required_args(["id", "pod", "container"])
    def get_logs(
        self,
        *,
        id: int,
        pod: str,
        container: str,
        lines: int = 100,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> TaskLogsRead:
        resp = self._get(
            f"/sieval/v1/tasks/{id}/logs",
            options=make_request_options(
                query={"pod": pod, "container": container, "lines": str(lines)},
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=DataResp[TaskLogsRead],
        )
        return resp.data

    @required_args(["id"])
    def get_reports_brief(
        self,
        *,
        id: int,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> List[TaskReportBrief]:
        resp = self._get(
            f"/sieval/v1/tasks/{id}/reports/brief",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=DataResp[List[TaskReportBrief]],
        )
        return resp.data

    @required_args(["id"])
    def get_reports_metrics(
        self,
        *,
        id: int,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> Dict[str, TaskLabelReport]:
        resp = self._get(
            f"/sieval/v1/tasks/{id}/reports/metrics",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=DataResp[Dict[str, TaskLabelReport]],
        )
        return resp.data

    @required_args(["id"])
    def get_reports_samples(
        self,
        *,
        id: int,
        case_id: int,
        iteration: int = 0,
        count: int = 15,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> List[TaskReportSample]:
        resp = self._get(
            f"/sieval/v1/tasks/{id}/reports/samples",
            options=make_request_options(
                query={
                    "case_id": str(case_id),
                    "iteration": str(iteration),
                    "page": "1",
                    "page_size": str(count),
                },
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=ListResp[TaskReportSample],
        )
        return resp.rows


class SiEvalTasksWithRawResponse:
    def __init__(self, tasks: SiEvalTasks) -> None:
        self.create = to_raw_response_wrapper(tasks.create)
        self.resubmit = to_raw_response_wrapper(tasks.resubmit)
        self.batch_resubmit = to_raw_response_wrapper(tasks.batch_resubmit)
        self.delete = to_raw_response_wrapper(tasks.delete)
        self.batch_delete = to_raw_response_wrapper(tasks.batch_delete)
        self.stop = to_raw_response_wrapper(tasks.stop)
        self.batch_stop = to_raw_response_wrapper(tasks.batch_stop)
        self.get = to_raw_response_wrapper(tasks.get)
        self.list = to_raw_response_wrapper(tasks.list)
        self.get_pods = to_raw_response_wrapper(tasks.get_pods)
        self.get_logs = to_raw_response_wrapper(tasks.get_logs)
        self.get_reports_brief = to_raw_response_wrapper(tasks.get_reports_brief)
        self.get_reports_metrics = to_raw_response_wrapper(tasks.get_reports_metrics)
        self.get_reports_samples = to_raw_response_wrapper(tasks.get_reports_samples)


__all__ = ["SiEvalTasks", "SiEvalTasksWithRawResponse"]
