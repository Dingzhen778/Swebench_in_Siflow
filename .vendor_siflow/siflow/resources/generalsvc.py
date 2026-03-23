from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

import httpx

from siflow._response import to_raw_response_wrapper
from siflow.types.generalsvc import CreateGeneralsvcRequest, ListGeneralsvcsResponse
from siflow.types.workflow import BasicResponse


from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven

from .._resource import SyncAPIResource

from .._base_client import make_request_options

if TYPE_CHECKING:
    from .._client import SiFlow


__all__ = ["GeneralSvc", "GeneralSvcWithRawResponse"]


class GeneralSvc(SyncAPIResource):
    with_raw_response: GeneralSvcWithRawResponse

    def __init__(self, client: SiFlow) -> None:
        super().__init__(client)
        self.with_raw_response = GeneralSvcWithRawResponse(self)

    def create(
        self,
        *,
        request: CreateGeneralsvcRequest | Dict[str, Any],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> BasicResponse:
        if isinstance(request, CreateGeneralsvcRequest):
            request_dict = request.model_dump(by_alias=True)
        else:
            request_dict = request.copy()
        
        return self._post(
            "/general-publish-service/v1/generalsvc",
            body=request_dict,
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
        name: Optional[str] | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> ListGeneralsvcsResponse:
        """列出GeneralSvc"""
        query: Query = {
            "page": str(page),
            "pageSize": str(page_size),
        }
        if name is not None:
            query["name"] = name
      

        resp = self._get(
            "/general-publish-service/v1/generalsvc",
            cast_to=ListGeneralsvcsResponse,
            options=make_request_options(
                query=query,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )
        return resp

    def delete(
        self,
        *,
        id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> BasicResponse:
        return self._delete(
            f"/general-publish-service/v1/generalsvc/{id}",
            cast_to=BasicResponse,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )  
 
    def offline(
        self,
        *,
        id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> BasicResponse:
        return self._post(
            f"/general-publish-service/v1/generalsvc/{id}/offline",
            cast_to=BasicResponse,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )  
    
    def online(
        self,
        *,
        id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> BasicResponse:
        return self._post(
            f"/general-publish-service/v1/generalsvc/{id}/online",
            cast_to=BasicResponse,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )  
class GeneralSvcWithRawResponse:
    def __init__(self, generalSvc: GeneralSvc) -> None:
        self._generalSvc = generalSvc

    def create(self, *args, **kwargs) -> httpx.Response:  # type: ignore[override]
        return to_raw_response_wrapper(self._generalSvc.create)(*args, **kwargs)

    def list(self, *args, **kwargs) -> httpx.Response:  # type: ignore[override]
        return to_raw_response_wrapper(self._generalSvc.list)(*args, **kwargs)

    def delete(self, *args, **kwargs) -> httpx.Response:  # type: ignore[override]
        return to_raw_response_wrapper(self._generalSvc.delete)(*args, **kwargs)
    
    def offline(self, *args, **kwargs) -> httpx.Response:  # type: ignore[override]
        return to_raw_response_wrapper(self._generalSvc.offline)(*args, **kwargs)
    
    def online(self, *args, **kwargs) -> httpx.Response:  # type: ignore[override]
        return to_raw_response_wrapper(self._generalSvc.online)(*args, **kwargs)