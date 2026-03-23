from __future__ import annotations

from typing import TYPE_CHECKING, List
from typing_extensions import Literal

import httpx

from ..types import DataListResp, DatasetVolume
from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._types import NOT_GIVEN, NotGiven
from .._resource import SyncAPIResource
from .._response import to_raw_response_wrapper
from .._base_client import make_request_options

if TYPE_CHECKING:
    from .._client import SiFlow


__all__ = ["Datasets", "DatasetsWithRawResponse"]


class Datasets(SyncAPIResource):
    with_raw_response: DatasetsWithRawResponse
    
    def __init__(self, client: SiFlow) -> None:
        super().__init__(client)
        self.with_raw_response = DatasetsWithRawResponse(self)

    def list(
        self,
        *,
        count: int = 10000,
        name: str | None = None,
        type: Literal["preset", "custom"] | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> List[DatasetVolume]:
        query: Query = {
            "page": "1", 
            "pageSize": str(count),
        }
        if name is not None:
            query["name"] = name
        if type is not None:
            query["variant"] = type
        resp = self._get(
            "/data-service/v1/datasets",
            cast_to=DataListResp[DatasetVolume],
            options=make_request_options(
                query=query,
                timeout=timeout,
                extra_headers=extra_headers, 
                extra_query=extra_query, 
                extra_body=extra_body, 
            ),
        )
        return resp.data


class DatasetsWithRawResponse:
    def __init__(self, datasets: Datasets) -> None:
        self.list = to_raw_response_wrapper(datasets.list)  # type: ignore
