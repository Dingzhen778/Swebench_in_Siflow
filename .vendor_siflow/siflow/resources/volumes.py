from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional
from typing_extensions import Literal

import httpx

from ..types import (
    VolumeQuota,
    VolumeQuotaDetail,
    VolumeItem,
    ListVolumesResp,
    VolumeIdName,
    CommonResponse,
    DataResp,
)
from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._utils import required_args, maybe_transform, is_given
from .._resource import SyncAPIResource
from .._response import to_raw_response_wrapper
from .._base_client import make_request_options

if TYPE_CHECKING:
    from .._client import SiFlow


__all__ = ["Volumes", "VolumesWithRawResponse"]


class Volumes(SyncAPIResource):
    with_raw_response: VolumesWithRawResponse

    def __init__(self, client: SiFlow) -> None:
        super().__init__(client)
        self.with_raw_response = VolumesWithRawResponse(self)

    def get_quota(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> CommonResponse:
        """获取存储配额"""
        resp = self._get(
            "/resource-service/v1/volume/quota",
            cast_to=CommonResponse,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )
        return resp

    def get_quota_detail(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> CommonResponse:
        """获取存储配额详情"""
        resp = self._get(
            "/resource-service/v1/volume/quota-detail",
            cast_to=CommonResponse,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )
        return resp

    def get_volume(
        self,
        id: int,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> VolumeItem:
        """获取单个Volume详情"""
        resp = self._get(
            f"/resource-service/v1/volume/{id}",
            cast_to=DataResp[VolumeItem],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )
        return resp.data

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 15,
        name: Optional[str] | None = None,
        tenant_name: Optional[str] | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> ListVolumesResp:
        """列出Volume"""
        query: Query = {
            "page": str(page),
            "pageSize": str(page_size),
        }
        if name is not None:
            query["name"] = name
        if tenant_name is not None:
            query["tenantName"] = tenant_name

        resp = self._get(
            "/resource-service/v1/volumes",
            cast_to=ListVolumesResp,
            options=make_request_options(
                query=query,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )
        return resp

    def get_user_volumes(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> CommonResponse:
        """获取用户Volume"""
        resp = self._get(
            "/resource-service/v1/user-volumes",
            cast_to=CommonResponse,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )
        return resp


class VolumesWithRawResponse:
    def __init__(self, volumes: Volumes) -> None:
        self._volumes = volumes

    def get_quota(
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
        return self._volumes._get(
            "/resource-service/v1/volume/quota",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=httpx.Response,
        )

    def get_quota_detail(
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
        return self._volumes._get(
            "/resource-service/v1/volume/quota-detail",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=httpx.Response,
        )

    def get_volume(
        self,
        id: int,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> httpx.Response:
        """
        Raw response. For low-level, direct access to HTTP response details.
        """
        return self._volumes._get(
            f"/resource-service/v1/volume/{id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=httpx.Response,
        )

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 15,
        name: Optional[str] | None = None,
        tenant_name: Optional[str] | None = None,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> httpx.Response:
        """
        Raw response. For low-level, direct access to HTTP response details.
        """
        query: Query = {
            "page": str(page),
            "pageSize": str(page_size),
        }
        if name is not None:
            query["name"] = name
        if tenant_name is not None:
            query["tenantName"] = tenant_name

        return self._volumes._get(
            "/resource-service/v1/volumes",
            options=make_request_options(
                query=query,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=httpx.Response,
        )

    def get_user_volumes(
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
        return self._volumes._get(
            "/resource-service/v1/user-volumes",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=httpx.Response,
        ) 