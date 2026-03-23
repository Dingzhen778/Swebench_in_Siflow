from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

import httpx

from ..types.schedule_strategy import (
    NodeScheduleStrategyCreateParams,
    NodeScheduleStrategyListResponse,
    NodeScheduleStrategyScope,
    NodeScheduleStrategyType,
    NodeScheduleStrategyUpdateParams,
    NodeScheduleStrategyWorkloadType,
)
from ..types import CommonResponse
from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._utils import required_args, maybe_transform
from .._resource import SyncAPIResource
from .._response import to_raw_response_wrapper
from .._base_client import make_request_options

if TYPE_CHECKING:
    from .._client import SiFlow


__all__ = ["NodeScheduleStrategies", "NodeScheduleStrategiesWithRawResponse"]


class NodeScheduleStrategies(SyncAPIResource):
    with_raw_response: NodeScheduleStrategiesWithRawResponse
    _ALLOWED_WORKLOAD_TYPES = {
        "task",
        "llm-service",
        "deployment",
        "vscs",
        "jupyter",
        "general-service",
    }

    def __init__(self, client: SiFlow) -> None:
        super().__init__(client)
        self.with_raw_response = NodeScheduleStrategiesWithRawResponse(self)

    @staticmethod
    def _validate_scope(scope: str) -> None:
        if scope not in {"user", "tenant"}:
            raise ValueError("scope must be one of: user, tenant")

    @classmethod
    def _validate_workload_types(cls, workload_types: List[str]) -> None:
        if not workload_types:
            raise ValueError("workload_types must be a non-empty enum list")
        invalid = [t for t in workload_types if t not in cls._ALLOWED_WORKLOAD_TYPES]
        if invalid:
            allowed = ", ".join(sorted(cls._ALLOWED_WORKLOAD_TYPES))
            raise ValueError(f"invalid workload_types: {invalid}. allowed values: {allowed}")

    @required_args(["scope", "node_names", "workload_types", "expire_at"])
    def create(
        self,
        *,
        scope: NodeScheduleStrategyScope,
        node_names: List[str],
        expire_at: int,
        type: NodeScheduleStrategyType = "NodeNotIn",
        workload_types: List[NodeScheduleStrategyWorkloadType],
        reason: Optional[str] = None,
        source: Optional[str] = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> CommonResponse:
        self._validate_scope(scope)
        self._validate_workload_types(workload_types)
        params = {
            "scope": scope,
            "nodeNames": node_names,
            "type": type,
            "workloadTypes": workload_types,
            "expireAt": expire_at,
            "reason": reason,
            "source": source,
        }

        resp = self._post(
            "/resource-service/v1/node-blacklists",
            body=maybe_transform(params, NodeScheduleStrategyCreateParams),
            cast_to=CommonResponse,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )
        return resp

    def list(
        self,
        *,
        scope: Optional[NodeScheduleStrategyScope] = None,
        page: int = 1,
        page_size: int = 20,
        only_enabled: bool = False,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> NodeScheduleStrategyListResponse:
        query: Query = {
            "page": str(page),
            "pageSize": str(page_size),
            "onlyEnabled": str(only_enabled).lower(),
        }
        if scope is not None:
            self._validate_scope(scope)
            query["scope"] = scope

        resp = self._get(
            "/resource-service/v1/node-blacklists",
            cast_to=NodeScheduleStrategyListResponse,
            options=make_request_options(
                query=query,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )
        return resp

    @required_args(["id"])
    def disable(
        self,
        *,
        id: int,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> CommonResponse:
        resp = self._delete(
            f"/resource-service/v1/node-blacklists/{id}",
            cast_to=CommonResponse,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )
        return resp

    @required_args(["id", "scope", "expire_at"])
    def update(
        self,
        *,
        id: int,
        scope: NodeScheduleStrategyScope,
        expire_at: int,
        node_name: Optional[str] = None,
        type: NodeScheduleStrategyType = "NodeNotIn",
        workload_types: Optional[List[NodeScheduleStrategyWorkloadType]] = None,
        reason: Optional[str] = None,
        source: Optional[str] = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> CommonResponse:
        self._validate_scope(scope)
        if workload_types is not None:
            self._validate_workload_types(workload_types)
        params = {
            "id": id,
            "scope": scope,
            "nodeName": node_name,
            "type": type,
            "workloadTypes": workload_types,
            "expireAt": expire_at,
            "reason": reason,
            "source": source,
        }

        resp = self._put(
            "/resource-service/v1/node-blacklists",
            body=maybe_transform(params, NodeScheduleStrategyUpdateParams),
            cast_to=CommonResponse,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )
        return resp


class NodeScheduleStrategiesWithRawResponse:
    def __init__(self, node_schedule_strategies: NodeScheduleStrategies) -> None:
        self.create = to_raw_response_wrapper(node_schedule_strategies.create)  # type: ignore
        self.list = to_raw_response_wrapper(node_schedule_strategies.list)  # type: ignore
        self.disable = to_raw_response_wrapper(node_schedule_strategies.disable)  # type: ignore
        self.update = to_raw_response_wrapper(node_schedule_strategies.update)  # type: ignore
