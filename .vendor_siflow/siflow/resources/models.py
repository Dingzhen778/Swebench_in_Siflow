from __future__ import annotations

from typing import TYPE_CHECKING, List
from typing_extensions import Literal

import httpx

from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._utils import required_args
from .._resource import SyncAPIResource
from .._response import to_raw_response_wrapper
from .._base_client import make_request_options
from ..types import ListResp, Model 

if TYPE_CHECKING:
    from .._client import SiFlow


__all__ = ["Models", "ModelsWithRawResponse"]


class Models(SyncAPIResource):
    with_raw_response: ModelsWithRawResponse
    
    def __init__(self, client: SiFlow) -> None:
        super().__init__(client)
        self.with_raw_response = ModelsWithRawResponse(self)
        
    @required_args(["type"])
    def list(
        self,
        *,
        type: Literal["preset", "custom"],
        count: int = 10000,
        name: str | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> List[Model]: # type: ignore
        query: Query = {
            "page": "1", 
            "pageSize": str(count),
        }
        if name is not None:
            query["name"] = name
            
        if type == "preset":
            url = "/model-service/v1/preset-models"
        else:
            url = "/model-service/v1/models"
        resp = self._get(url,
            cast_to=ListResp[Model],
            options=make_request_options(
                query=query,
                timeout=timeout,
                extra_headers=extra_headers, 
                extra_query=extra_query, 
                extra_body=extra_body, 
            )
        )
        return resp.rows


class ModelsWithRawResponse:
    def __init__(self, models: Models) -> None:
        self.list = to_raw_response_wrapper(models.list)  # type: ignore
