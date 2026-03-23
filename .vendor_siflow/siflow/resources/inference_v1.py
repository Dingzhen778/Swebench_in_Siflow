from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Dict, Any

import httpx
from siflow.types.workflow import BasicResponse
from ..types import (
    DataResp,
)
from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._utils import required_args
from .._resource import SyncAPIResource
from .._response import to_raw_response_wrapper
from .._base_client import make_request_options
from siflow.types.inference_v1 import CreateDeploymentRequest, ListDeploymentsResponse, DeploymentInfo, UpdateDeploymentRequest
if TYPE_CHECKING:
    from .._client import SiFlow



__all__ = [
    "InferenceV1", 
    "InferenceV1WithRawResponse",
]


class InferenceV1(SyncAPIResource):
    with_raw_response: InferenceV1WithRawResponse

    def __init__(self, client: SiFlow) -> None:
        super().__init__(client)
        self.with_raw_response = InferenceV1WithRawResponse(self)

    def create(
        self,
        *,
        request: CreateDeploymentRequest | Dict[str, Any],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> BasicResponse:
        if isinstance(request, CreateDeploymentRequest):
            request_dict = request.model_dump(by_alias=True)
        else:
            request_dict = request.copy()
        return self._post(  # type: ignore
            "/inference-service/v1/deployments",
            body=request_dict,
            cast_to=BasicResponse,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )

    def delete(
        self,
        *,
        id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> BasicResponse:

        return self._delete(  # type: ignore
            f"/inference-service/v1/deployments/{id}",
            cast_to=BasicResponse,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )

   
    def update(
        self,
        *,
        id: str,
        request: UpdateDeploymentRequest | Dict[str, Any],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> BasicResponse:
        if isinstance(request, UpdateDeploymentRequest):
            request_dict = request.model_dump(by_alias=True)
        else:
            request_dict = request.copy()
        return self._put(  # type: ignore
            f"/inference-service/v1/deployments/{id}",
            body=request_dict,
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DataResp[str],  # type: ignore
        )

    def get(
        self,
        *,
        id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> DeploymentInfo:
        resp = self._get(  # type: ignore
            f"/inference-service/v1/deployments/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DataResp[Dict[str, Any]],  # type: ignore
        )
        return resp.data  # type: ignore

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
        name: Optional[str] = None,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> ListDeploymentsResponse:
        query: Dict[str, Any] = {
            "page": page,
            "pageSize": page_size,
        }
        if status is not None:
            query["status"] = status
        if name is not None:
            query["name"] = name
       

        resp = self._get(  # type: ignore
            "/inference-service/v1/deployments",
            cast_to=ListDeploymentsResponse,
            options=make_request_options(
                query=query,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )
        return resp  # type: ignore

   
    @required_args(["deployment_uuid"])
    def get_deployment_pods(
        self,
        *,
        deployment_uuid: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> List[Dict[str, Any]]:
        """Get deployment pods
        
        Args:
            deployment_uuid: Deployment UUID
            
        Returns:
            List of pods
        """
        resp = self._get(  # type: ignore
            f"/inference-service/v1/deployments/{deployment_uuid}/pods",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DataResp[List[Dict[str, Any]]],  # type: ignore
        )
        return resp.data  # type: ignore




class InferenceV1WithRawResponse:
    def __init__(self, inference_v1: InferenceV1) -> None:
        self.create_deployment = to_raw_response_wrapper(
            inference_v1.create,
        )
        self.delete_deployment = to_raw_response_wrapper(
            inference_v1.delete,
        )
    
        self.update_deployment = to_raw_response_wrapper(
            inference_v1.update,
        )
        self.get_deployment = to_raw_response_wrapper(
            inference_v1.get,
        )
        self.list_deployments = to_raw_response_wrapper(
            inference_v1.list,
        )
        self.get_deployment_pods = to_raw_response_wrapper(
            inference_v1.get_deployment_pods,
        )

        

