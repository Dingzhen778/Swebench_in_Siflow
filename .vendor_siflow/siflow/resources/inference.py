from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Dict

import httpx

from ..types import (
    Service,
    ServiceBrief,
    ServiceCreateParams,
    ServiceUpdateParams,
    ServiceScaleParams,
    ServiceCreateResp,
    ServiceUpdateResp,
    ServiceDeleteResp,
    Instance,
    ListInstanceResponse,
    EngineVersion,
    EngineVersionCreateParams,
    EngineVersionCreateResp,
    EngineOption,
    ServiceVersion,
    DataResp,
    ListResp,
)
from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._utils import required_args
from .._resource import SyncAPIResource
from .._response import to_raw_response_wrapper
from .._base_client import make_request_options

if TYPE_CHECKING:
    from .._client import SiFlow


__all__ = ["Inference", "InferenceWithRawResponse"]


class Inference(SyncAPIResource):
    with_raw_response: InferenceWithRawResponse

    def __init__(self, client: SiFlow) -> None:
        super().__init__(client)
        self.with_raw_response = InferenceWithRawResponse(self)

    @required_args(["service_params"])
    def create_service(
        self,
        *,
        service_params: ServiceCreateParams,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> int:
        """Create a new inference service
        
        Args:
            service_params: Service creation parameters
            
        Returns:
            Service ID
        """
        resp = self._post(  # type: ignore
            "/inference-service/v1/llm/service",
            body=service_params.model_dump(by_alias=True),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ServiceCreateResp,  # type: ignore
        )
        return resp.data  # type: ignore

    @required_args(["service_id", "service_params"])
    def update_service(
        self,
        *,
        service_id: int,
        service_params: ServiceUpdateParams,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> int:
        """Update an existing inference service
        
        Args:
            service_id: Service ID to update
            service_params: Service update parameters
            
        Returns:
            Service ID
        """
        resp = self._put(  # type: ignore
            f"/inference-service/v1/llm/service/{service_id}",
            body=service_params.model_dump(by_alias=True),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ServiceUpdateResp,  # type: ignore
        )
        return resp.data  # type: ignore

    @required_args(["service_id"])
    def cancel_update_service(
        self,
        *,
        service_id: int,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> int:
        """Cancel service update
        
        Args:
            service_id: Service ID to cancel update for
            
        Returns:
            Service ID
        """
        resp = self._post(  # type: ignore
            f"/inference-service/v1/llm/service/{service_id}/cancel-update",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ServiceUpdateResp,  # type: ignore
        )
        return resp.data  # type: ignore

    @required_args(["service_id"])
    def rollback_service(
        self,
        *,
        service_id: int,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> int:
        """Rollback service to previous version
        
        Args:
            service_id: Service ID to rollback
            
        Returns:
            Service ID
        """
        resp = self._post(  # type: ignore
            f"/inference-service/v1/llm/service/{service_id}/rollback",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ServiceUpdateResp,  # type: ignore
        )
        return resp.data  # type: ignore

    @required_args(["service_id", "version"])
    def rollback_service_to_version(
        self,
        *,
        service_id: int,
        version: int,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> int:
        """Rollback service to specific version
        
        Args:
            service_id: Service ID to rollback
            version: Target version number
            
        Returns:
            Service ID
        """
        resp = self._post(  # type: ignore
            f"/inference-service/v1/llm/service/{service_id}/version/{version}/rollback",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ServiceUpdateResp,  # type: ignore
        )
        return resp.data  # type: ignore

    @required_args(["service_id", "scale_params"])
    def scale_service(
        self,
        *,
        service_id: int,
        scale_params: ServiceScaleParams,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> ServiceScaleParams:
        """Scale service instances
        
        Args:
            service_id: Service ID to scale
            scale_params: Scale parameters
            
        Returns:
            Scale parameters
        """
        resp = self._put(  # type: ignore
            f"/inference-service/v1/llm/service/{service_id}/scale",
            body=scale_params.model_dump(by_alias=True),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ServiceUpdateResp,  # type: ignore
        )
        return resp  # type: ignore

    @required_args(["service_id"])
    def stop_scale_service(
        self,
        *,
        service_id: int,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> int:
        """Stop service scaling
        
        Args:
            service_id: Service ID to stop scaling for
            
        Returns:
            Service ID
        """
        resp = self._post(  # type: ignore
            f"/inference-service/v1/llm/service/{service_id}/stop-scale",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ServiceUpdateResp,  # type: ignore
        )
        return resp.data  # type: ignore

    @required_args(["service_id"])
    def get_service(
        self,
        *,
        service_id: int,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> Service:
        """Get service details
        
        Args:
            service_id: Service ID to get
            
        Returns:
            Service details
        """
        resp = self._get(  # type: ignore
            f"/inference-service/v1/llm/service/{service_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DataResp[Service],
        )
        return resp.data  # type: ignore

    def list_services(
        self,
        *,
        id: Optional[str] = None,
        tenant: Optional[str] = None,
        owner: Optional[str] = None,
        status: Optional[str] = None,
        name: Optional[str] = None,
        page: int = 1,
        page_size: int = 15,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> List[ServiceBrief]:
        """List services with optional filtering
        
        Args:
            id: Filter by service ID
            tenant: Filter by tenant
            owner: Filter by owner
            status: Filter by status
            name: Filter by name
            page: Page number
            page_size: Page size
            
        Returns:
            List of service briefs
        """
        query: Query = {
            "page": str(page),
            "pageSize": str(page_size),
        }
        if id is not None:
            query["id"] = id
        if tenant is not None:
            query["tenant"] = tenant
        if owner is not None:
            query["owner"] = owner
        if status is not None:
            query["status"] = status
        if name is not None:
            query["name"] = name
            
        resp = self._get(  # type: ignore
            "/inference-service/v1/llm/services",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=query,
            ),
            cast_to=ListResp[ServiceBrief],  # type: ignore
        )
        return resp.rows or []  # type: ignore

    @required_args(["service_id"])
    def offline_service(
        self,
        *,
        service_id: int,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> int:
        """Take service offline
        
        Args:
            service_id: Service ID to take offline
            
        Returns:
            Service ID
        """
        resp = self._delete(  # type: ignore
            f"/inference-service/v1/llm/service/{service_id}/offline",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ServiceDeleteResp,  # type: ignore
        )
        return resp.data  # type: ignore

    @required_args(["service_id"])
    def online_service(
        self,
        *,
        service_id: int,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> int:
        """Bring service online
        
        Args:
            service_id: Service ID to bring online
            
        Returns:
            Service ID
        """
        resp = self._post(  # type: ignore
            f"/inference-service/v1/llm/service/{service_id}/online",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ServiceUpdateResp,  # type: ignore
        )
        return resp.data  # type: ignore

    @required_args(["service_id"])
    def delete_service(
        self,
        *,
        service_id: int,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> int:
        """Delete service permanently
        
        Args:
            service_id: Service ID to delete
            
        Returns:
            Service ID
        """
        resp = self._delete(  # type: ignore
            f"/inference-service/v1/llm/service/{service_id}/delete",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ServiceDeleteResp,  # type: ignore
        )
        return resp.data  # type: ignore
        
    @required_args(["service_ids"])
    def batch_online_service(
        self,
        *,
        service_ids: List[int],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> List[int]:
        """Bring multiple services online in batch
        
        Args:
            service_ids: List of service IDs to bring online
            
        Returns:
            List of service IDs that were brought online
        """
        resp = self._post(  # type: ignore
            f"/inference-service/v1/llm/service/batch/online",
            body={"serviceIDs": service_ids},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ListResp[int],  # type: ignore
        )
        return resp.rows or []  # type: ignore
        
    @required_args(["service_ids"])
    def batch_offline_service(
        self,
        *,
        service_ids: List[int],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> List[int]:
        """Take multiple services offline in batch
        
        Args:
            service_ids: List of service IDs to take offline
            
        Returns:
            List of service IDs that were taken offline
        """
        resp = self._post(  # type: ignore
            f"/inference-service/v1/llm/service/batch/offline",
            body={"serviceIDs": service_ids},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ListResp[int],  # type: ignore
        )
        return resp.rows or []  # type: ignore
        
    @required_args(["service_ids"])    
    def batch_delete_service(
        self,
        *,
        service_ids: List[int],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> List[int]:
        """Delete multiple services permanently in batch
        
        Args:
            service_ids: List of service IDs to delete
            
        Returns:
            List of service IDs that were deleted
        """
        resp = self._post(  # type: ignore
            f"/inference-service/v1/llm/service/batch/delete",
            body={"serviceIDs": service_ids},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ListResp[int],  # type: ignore
        )
        return resp.rows or []  # type: ignore
        
    @required_args(["names"])
    def batch_delete_service_by_name(
        self,
        *,
        names: List[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> List[str]:
        """Delete multiple services permanently in batch by name
        
        Args:
            names: List of service names to delete
            
        Returns:
            List of service names that were deleted
        """
        resp = self._post(  # type: ignore
            f"/inference-service/v1/llm/service/batch/delete-by-name",
            body={"names": names},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ListResp[str],  # type: ignore
        )
        return resp.rows or []  # type: ignore
        
    @required_args(["names"])
    def batch_online_service_by_name(
        self,
        *,
        names: List[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> List[str]:
        """Bring multiple services online in batch by name
        
        Args:
            names: List of service names to bring online
            
        Returns:
            List of service names that were brought online
        """
        resp = self._post(  # type: ignore
            f"/inference-service/v1/llm/service/batch/online-by-name",
            body={"names": names},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ListResp[str],  # type: ignore
        )
        return resp.rows or []  # type: ignore
        
    @required_args(["names"])
    def batch_offline_service_by_name(
        self,
        *,
        names: List[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> List[str]:
        """Take multiple services offline in batch by name
        
        Args:
            names: List of service names to take offline
            
        Returns:
            List of service names that were taken offline
        """
        resp = self._post(  # type: ignore
            f"/inference-service/v1/llm/service/batch/offline-by-name",
            body={"names": names},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ListResp[str],  # type: ignore
        )
        return resp.rows or []  # type: ignore

    @required_args(["engine_params"])
    def create_engine_version(
        self,
        *,
        engine_params: EngineVersionCreateParams,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> int:
        """Create engine version
        
        Args:
            engine_params: Engine version creation parameters
            
        Returns:
            Engine version ID
        """
        resp = self._post(  # type: ignore
            "/inference-service/v1/llm/engine",
            body=engine_params.model_dump(by_alias=True),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EngineVersionCreateResp,  # type: ignore
        )
        return resp.data  # type: ignore

    def list_engine_versions(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> List[EngineVersion]:
        """List engine versions
        
        Returns:
            List of engine versions
        """
        resp = self._get(  # type: ignore
            "/inference-service/v1/llm/engines",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ListResp[EngineVersion],  # type: ignore
        )
        return resp.rows or []  # type: ignore

    def list_engine_options(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> List[EngineOption]:
        """List engine options
        
        Returns:
            List of engine options
        """
        resp = self._get(  # type: ignore
            "/inference-service/v1/llm/engine-options",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ListResp[EngineOption],  # type: ignore
        )
        return resp.rows or []  # type: ignore

    @required_args(["service_id"])
    def list_service_versions(
        self,
        *,
        service_id: int,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> List[ServiceVersion]:
        """List service versions
        
        Args:
            service_id: Service ID to get versions for
            
        Returns:
            List of service versions
        """
        resp = self._get(  # type: ignore
            f"/inference-service/v1/llm/service/{service_id}/versions",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ListResp[ServiceVersion],  # type: ignore
        )
        return resp.rows or []  # type: ignore

    @required_args(["service_id", "service_params"])
    def update_service_register(
        self,
        *,
        service_id: int,
        service_params: ServiceUpdateParams,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> int:
        """Update service registration
        
        Args:
            service_id: Service ID to update registration for
            service_params: Service parameters
            
        Returns:
            Service ID
        """
        resp = self._put(  # type: ignore
            f"/inference-service/v1/llm/service/{service_id}/register",
            body=service_params.model_dump(by_alias=True),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ServiceUpdateResp,  # type: ignore
        )
        return resp.data  # type: ignore

    @required_args(["service_id"])
    def list_service_instances(
        self,
        *,
        service_id: int,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> Dict[str, List[Instance]]:
        """List service instances (pods)
        
        Args:
            service_id: Service ID to get instances for
            
        Returns:
            Dictionary mapping role types to instance lists
        """
        resp = self._get(  # type: ignore
            f"/inference-service/v1/llm/service/{service_id}/pods",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ListInstanceResponse,  # type: ignore
        )
        return resp.rows or {}  # type: ignore

    @required_args(["service_id", "pod_name"])
    def recreate_instance(
        self,
        *,
        service_id: int,
        pod_name: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> int:
        """Recreate service instance
        
        Args:
            service_id: Service ID
            pod_name: Pod name to recreate
            
        Returns:
            Service ID
        """
        resp = self._post(  # type: ignore
            f"/inference-service/v1/llm/service/{service_id}/pods/{pod_name}/recreate",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ServiceUpdateResp,  # type: ignore
        )
        return resp.data  # type: ignore



class InferenceWithRawResponse:
    def __init__(self, inference: Inference) -> None:
        self.create_service = to_raw_response_wrapper(inference.create_service)
        self.update_service = to_raw_response_wrapper(inference.update_service)
        self.cancel_update_service = to_raw_response_wrapper(inference.cancel_update_service)
        self.rollback_service = to_raw_response_wrapper(inference.rollback_service)
        self.rollback_service_to_version = to_raw_response_wrapper(inference.rollback_service_to_version)
        self.scale_service = to_raw_response_wrapper(inference.scale_service)
        self.stop_scale_service = to_raw_response_wrapper(inference.stop_scale_service)
        self.get_service = to_raw_response_wrapper(inference.get_service)
        self.list_services = to_raw_response_wrapper(inference.list_services)
        self.offline_service = to_raw_response_wrapper(inference.offline_service)
        self.online_service = to_raw_response_wrapper(inference.online_service)
        self.delete_service = to_raw_response_wrapper(inference.delete_service)
        self.create_engine_version = to_raw_response_wrapper(inference.create_engine_version)
        self.list_engine_versions = to_raw_response_wrapper(inference.list_engine_versions)
        self.list_engine_options = to_raw_response_wrapper(inference.list_engine_options)
        self.list_service_versions = to_raw_response_wrapper(inference.list_service_versions)
        self.update_service_register = to_raw_response_wrapper(inference.update_service_register)
        self.list_service_instances = to_raw_response_wrapper(inference.list_service_instances)
        self.recreate_instance = to_raw_response_wrapper(inference.recreate_instance)
        self.batch_delete_service_by_name = to_raw_response_wrapper(inference.batch_delete_service_by_name)
        self.batch_online_service_by_name = to_raw_response_wrapper(inference.batch_online_service_by_name)
        self.batch_offline_service_by_name = to_raw_response_wrapper(inference.batch_offline_service_by_name)
