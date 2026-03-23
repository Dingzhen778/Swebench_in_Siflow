from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional
from typing_extensions import Literal

import httpx

from ..types import (
    ListOndemandInstanceLimitReq,
    ConfigMapInstanceInfo,
    ListInstanceQuotOrderItem,
    ListOndemandInstanceLimitItem,
    ListInstanceQuotaReq,
    InstanceQuotaItem,
    InstanceSummaryResponse,
    UserInstanceUsageInfo,
    ResourcePoolItem,
    UserInstanceUsage,
    CommonResponse,
    MeteringResponse,
)
from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._utils import required_args, maybe_transform, is_given
from .._resource import SyncAPIResource
from .._response import to_raw_response_wrapper
from .._base_client import make_request_options

if TYPE_CHECKING:
    from .._client import SiFlow


__all__ = ["Instances", "InstancesWithRawResponse"]


class Instances(SyncAPIResource):
    with_raw_response: InstancesWithRawResponse

    def __init__(self, client: SiFlow) -> None:
        super().__init__(client)
        self.with_raw_response = InstancesWithRawResponse(self)

    def list_ondemand(
        self,
        *,
        region: str,
        cluster: Optional[str] | None = None,
        tenant_name: Optional[str] | None = None,
        page: int = 1,
        page_size: int = 10,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> CommonResponse:
        """获取按需实例配额列表"""
        query: Query = {
            "region": region,
            "page": str(page),
            "pageSize": str(page_size),
        }
        if cluster is not None:
            query["cluster"] = cluster
        if tenant_name is not None:
            query["tenantName"] = tenant_name

        resp = self._get(
            "/resource-service/v1/instances/ondemand",
            cast_to=CommonResponse,
            options=make_request_options(
                query=query,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )
        return resp

    def get_ondemand_metering(
        self,
        *,
        start_time: str,
        end_time: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> MeteringResponse:
        """获取按需实例计量数据"""
        query: Query = {
            "startTime": start_time,
            "endTime": end_time,
        }
        resp = self._get(
            "/resource-service/v1/instances/ondemand-metering",
            cast_to=MeteringResponse,
            options=make_request_options(
                query=query,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )
        return resp

    def get_quota_info(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> CommonResponse:
        """获取实例配额信息"""
        resp = self._get(
            "/resource-service/v1/instance/quota",
            cast_to=CommonResponse,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )
        return resp

    def list_available(
        self,
        *,
        region: str,
        cluster: Optional[str] | None = None,
        status: Optional[str] | None = None,
        tenant_name: Optional[str] | None = None,
        page: int = 1,
        page_size: int = 10,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> CommonResponse:
        """获取可用实例订单列表"""
        query: Query = {
            "region": region,
            "page": str(page),
            "pageSize": str(page_size),
        }
        if cluster is not None:
            query["cluster"] = cluster
        if status is not None:
            query["status"] = status
        if tenant_name is not None:
            query["tenantName"] = tenant_name

        resp = self._get(
            "/resource-service/v1/instances/available",
            cast_to=CommonResponse,
            options=make_request_options(
                query=query,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )
        return resp

    def list_quotas(
        self,
        *,
        region: Optional[str] | None = None,
        cluster: Optional[str] | None = None,
        tenant_name: Optional[str] | None = None,
        resource_pool_qos_type: Optional[str] | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> CommonResponse:
        """获取实例配额列表"""
        query: Query = {}
        if region is not None:
            query["region"] = region
        if cluster is not None:
            query["cluster"] = cluster
        if tenant_name is not None:
            query["tenantName"] = tenant_name
        if resource_pool_qos_type is not None:
            query["resourcePoolQosType"] = resource_pool_qos_type

        resp = self._get(
            "/resource-service/v1/instances",
            cast_to=CommonResponse,
            options=make_request_options(
                query=query,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )
        return resp

    def get_user_instances(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> CommonResponse:
        """获取用户实例配额"""
        resp = self._get(
            "/resource-service/v1/user-instances",
            cast_to=CommonResponse,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )
        return resp

    def get_user_instances_pool(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> CommonResponse:
        """获取用户专属资源池配额"""
        resp = self._get(
            "/resource-service/v1/user-instances-pool",
            cast_to=CommonResponse,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )
        return resp

    def get_summary(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> InstanceSummaryResponse:
        """获取资源摘要"""
        resp = self._get(
            "/resource-service/v1/resources/summary",
            cast_to=InstanceSummaryResponse,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )
        return resp


class InstancesWithRawResponse:
    def __init__(self, instances: Instances) -> None:
        self._instances = instances

    def list_ondemand(
        self,
        *,
        region: str,
        cluster: Optional[str] | None = None,
        tenant_name: Optional[str] | None = None,
        page: int = 1,
        page_size: int = 10,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> httpx.Response:
        """
        Raw response. For low-level, direct access to HTTP response details.
        """
        query: Query = {
            "region": region,
            "page": str(page),
            "pageSize": str(page_size),
        }
        if cluster is not None:
            query["cluster"] = cluster
        if tenant_name is not None:
            query["tenantName"] = tenant_name

        return self._instances._get(
            "/resource-service/v1/instances/ondemand",
            options=make_request_options(
                query=query,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=httpx.Response,
        )

    def get_ondemand_metering(
        self,
        *,
        start_time: str,
        end_time: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> httpx.Response:
        """
        Raw response. For low-level, direct access to HTTP response details.
        """
        query: Query = {
            "startTime": start_time,
            "endTime": end_time,
        }
        return self._instances._get(
            "/resource-service/v1/instances/ondemand-metering",
            options=make_request_options(
                query=query,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=httpx.Response,
        )

    def get_quota_info(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> httpx.Response:
        """
        Raw response. For low-level, direct access to HTTP response details.
        """
        return self._instances._get(
            "/resource-service/v1/instance/quota",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=httpx.Response,
        )

    def list_available(
        self,
        *,
        region: str,
        cluster: Optional[str] | None = None,
        status: Optional[str] | None = None,
        tenant_name: Optional[str] | None = None,
        page: int = 1,
        page_size: int = 10,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> httpx.Response:
        """
        Raw response. For low-level, direct access to HTTP response details.
        """
        query: Query = {
            "region": region,
            "page": str(page),
            "pageSize": str(page_size),
        }
        if cluster is not None:
            query["cluster"] = cluster
        if status is not None:
            query["status"] = status
        if tenant_name is not None:
            query["tenantName"] = tenant_name

        return self._instances._get(
            "/resource-service/v1/instances/available",
            options=make_request_options(
                query=query,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=httpx.Response,
        )

    def list_quotas(
        self,
        *,
        region: Optional[str] | None = None,
        cluster: Optional[str] | None = None,
        tenant_name: Optional[str] | None = None,
        resource_pool_qos_type: Optional[str] | None = None,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> httpx.Response:
        """
        Raw response. For low-level, direct access to HTTP response details.
        """
        query: Query = {}
        if region is not None:
            query["region"] = region
        if cluster is not None:
            query["cluster"] = cluster
        if tenant_name is not None:
            query["tenantName"] = tenant_name
        if resource_pool_qos_type is not None:
            query["resourcePoolQosType"] = resource_pool_qos_type

        return self._instances._get(
            "/resource-service/v1/instances",
            options=make_request_options(
                query=query,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=httpx.Response,
        )

    def get_user_instances(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> httpx.Response:
        """
        Raw response. For low-level, direct access to HTTP response details.
        """
        return self._instances._get(
            "/resource-service/v1/user-instances",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=httpx.Response,
        )

    def get_user_instances_pool(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> httpx.Response:
        """
        Raw response. For low-level, direct access to HTTP response details.
        """
        return self._instances._get(
            "/resource-service/v1/user-instances-pool",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=httpx.Response,
        )

    def get_summary(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> httpx.Response:
        """
        Raw response. For low-level, direct access to HTTP response details.
        """
        return self._instances._get(
            "/resource-service/v1/resources/summary",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=httpx.Response,
        ) 