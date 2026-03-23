from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional
from typing_extensions import Literal

import httpx

from ..types import (
    InstanceUserQuotaResp,
    CommonResponse,
)
from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._utils import required_args, maybe_transform, is_given
from .._resource import SyncAPIResource
from .._response import to_raw_response_wrapper
from .._base_client import make_request_options

if TYPE_CHECKING:
    from .._client import SiFlow


__all__ = ["Quotas", "QuotasWithRawResponse"]


class Quotas(SyncAPIResource):
    with_raw_response: QuotasWithRawResponse

    def __init__(self, client: SiFlow) -> None:
        super().__init__(client)
        self.with_raw_response = QuotasWithRawResponse(self)

    def get_user_quotas(
        self,
        *,
        id: Optional[str] = None,
        user_name: Optional[str] = None,
        instance_quota_id: Optional[str] = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> CommonResponse:
        """获取用户配额列表"""
        query: Query = {}
        if id is not None:
            query["id"] = id
        if user_name is not None:
            query["userName"] = user_name
        if instance_quota_id is not None:
            query["instanceQuotaId"] = instance_quota_id
        
        # 至少需要提供一个参数
        if not query:
            raise ValueError("必须提供 id、userName 或 instanceQuotaId 之一")
            
        resp = self._get(
            "/resource-service/v1/user-quota",
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


class QuotasWithRawResponse:
    def __init__(self, quotas: Quotas) -> None:
        self._quotas = quotas

    def get_user_quotas(
        self,
        *,
        id: Optional[str] = None,
        user_name: Optional[str] = None,
        instance_quota_id: Optional[str] = None,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> httpx.Response:
        """
        Raw response. For low-level, direct access to HTTP response details.
        """
        query: Query = {}
        if id is not None:
            query["id"] = id
        if user_name is not None:
            query["userName"] = user_name
        if instance_quota_id is not None:
            query["instanceQuotaId"] = instance_quota_id
        
        # 至少需要提供一个参数
        if not query:
            raise ValueError("必须提供 id、userName 或 instanceQuotaId 之一")
            
        return self._quotas._get(
            "/resource-service/v1/user-quota",
            options=make_request_options(
                query=query,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=httpx.Response,
        ) 