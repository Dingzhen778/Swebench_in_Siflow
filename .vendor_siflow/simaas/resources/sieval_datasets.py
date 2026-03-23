from __future__ import annotations

from typing import TYPE_CHECKING, List

import httpx

from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._utils import required_args
from .._resource import SyncAPIResource
from .._response import to_raw_response_wrapper
from .._base_client import make_request_options
from ..types.common import DataResp, ListResp
from ..types.sieval_datasets import DatasetRead, DatasetReadSimple

if TYPE_CHECKING:
    from .._client import SiMaas


class SiEvalDatasets(SyncAPIResource):
    with_raw_response: SiEvalDatasetsWithRawResponse

    def __init__(self, client: SiMaas) -> None:
        super().__init__(client)
        self.with_raw_response = SiEvalDatasetsWithRawResponse(self)

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
    ) -> DatasetRead:
        resp = self._get(
            f"/sieval/v1/datasets/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DataResp[DatasetRead],
        )
        return resp.data

    def list(
        self,
        *,
        count: int = 15,
        name: str | None = None,
        label_l1: str | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> List[DatasetReadSimple]:
        query: Query = {
            "page": "1",
            "page_size": str(count),
        }
        if name is not None:
            query["name"] = name
        if label_l1 is not None:
            query["label_l1"] = label_l1
        resp = self._get(
            "/sieval/v1/datasets",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=query,
            ),
            cast_to=ListResp[DatasetReadSimple],
        )
        return resp.rows


class SiEvalDatasetsWithRawResponse:
    def __init__(self, datasets: SiEvalDatasets) -> None:
        self.get = to_raw_response_wrapper(datasets.get)
        self.list = to_raw_response_wrapper(datasets.list)


__all__ = ["SiEvalDatasets", "SiEvalDatasetsWithRawResponse"]
