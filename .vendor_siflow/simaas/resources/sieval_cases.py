from __future__ import annotations

from typing import TYPE_CHECKING, List, Literal

import httpx

from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._utils import required_args
from .._resource import SyncAPIResource
from .._response import to_raw_response_wrapper
from .._base_client import make_request_options
from ..types.common import DataResp, ListResp
from ..types.sieval_cases import CaseRead, CaseReadSimple

if TYPE_CHECKING:
    from .._client import SiMaas


class SiEvalCases(SyncAPIResource):
    with_raw_response: SiEvalCasesWithRawResponse

    def __init__(self, client: SiMaas) -> None:
        super().__init__(client)
        self.with_raw_response = SiEvalCasesWithRawResponse(self)

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
    ) -> CaseRead:
        resp = self._get(
            f"/sieval/v1/cases/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DataResp[CaseRead],
        )
        return resp.data

    def list(
        self,
        *,
        count: int = 15,
        name: str | None = None,
        mode: Literal["gen", "ppl"] | None = None,
        judge: bool | None = None,
        sandbox: bool | None = None,
        dataset_id: int | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> List[CaseReadSimple]:
        query: Query = {
            "page": "1",
            "page_size": str(count),
        }
        if name is not None:
            query["name"] = name
        if mode is not None:
            query["mode"] = mode
        if judge is not None:
            query["judge"] = str(judge).lower()
        if sandbox is not None:
            query["sandbox"] = str(sandbox).lower()
        if dataset_id is not None:
            query["dataset_id"] = str(dataset_id)
        resp = self._get(
            "/sieval/v1/cases",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=query,
            ),
            cast_to=ListResp[CaseReadSimple],
        )
        return resp.rows


class SiEvalCasesWithRawResponse:
    def __init__(self, cases: SiEvalCases) -> None:
        self.get = to_raw_response_wrapper(cases.get)
        self.list = to_raw_response_wrapper(cases.list)


__all__ = ["SiEvalCases", "SiEvalCasesWithRawResponse"]
