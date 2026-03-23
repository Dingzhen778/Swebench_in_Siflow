from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional
from .._resource import SyncAPIResource
from .._response import to_raw_response_wrapper
from .._utils import required_args, maybe_transform
from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._base_client import make_request_options
import os
import httpx

__all__ = ["Images", "ImagesWithRawResponse"]

if TYPE_CHECKING:
    from .._client import SiFlow

from ..types import (
    ListResp,
    RegisterImageRequest,
    ImageBuildConfigRequest,
    InstanceRequest,
    ImageListResponse,
    RegisterImageResponse,
    ImageShareResp
)


class Images(SyncAPIResource):
    with_raw_response: ImagesWithRawResponse

    def __init__(self, client: SiFlow) -> None:
        super().__init__(client)
        self.with_raw_response = ImagesWithRawResponse(self)

    def create(
            self,
            *,
            name: str,
            version: str,
            major_category: Optional[str] = None,
            minor_category: Optional[str] = None,
            image_build_type: Optional[str] = None,  # e.g. preset/custom
            image_build_region: Optional[str] = None,
            image_build_cluster: Optional[str] = None,
            image_build_config: Optional[ImageBuildConfigRequest] = None,
            resource_pool: Optional[str] = None,
            instances: Optional[List[InstanceRequest]] = None,
            # 额外参数
            extra_headers: Optional[Headers] = None,
            extra_query: Optional[Query] = None,
            extra_body: Optional[Body] = None,
            timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> str:
        major_category = "siflow"
        config_data = image_build_config.dict(exclude_none=True) if image_build_config else None

        # 特殊处理 dockerfile_path
        if config_data:
            build_method = config_data.get("build_method")
            dockerfile_path = config_data.get("dockerfile_path")
            dockerfile_content = config_data.get("dockerfile_content")
            dockerfile_arg = config_data.get("dockerfile_arg")

            if dockerfile_arg and isinstance(dockerfile_arg, dict) and len(dockerfile_arg) > 0:
                config_data["dockerfile_arg"] = dockerfile_arg

            if build_method == "baseSiflowImage":
                config_data["build_method"] = "1"

            elif build_method == "baseDockerfile":
                config_data["build_method"] = "2"
                if dockerfile_path:
                    if os.path.exists(dockerfile_path):
                        with open(dockerfile_path, "r", encoding="utf-8") as f:
                            dockerfile_str = f.read()
                        config_data["dockerfile"] = dockerfile_str
                    else:
                        raise FileNotFoundError(f"Dockerfile path does not exist: {dockerfile_path}")
                else:
                    config_data["dockerfile"] = dockerfile_content

            elif build_method == "baseThirdImage":
                config_data["build_method"] = "3"

            elif build_method == "baseExistImage":
                config_data["build_method"] = "4"

            else:
                raise ValueError(f"Unsupported build_method: {build_method}")

        # 处理instances列表，将InstanceRequest对象转换为字典
        instances_data = None
        if instances:
            instances_data = [instance.dict(exclude_none=True) for instance in instances]

        data = {
            "name": name,
            "major_category": major_category,
            "minor_category": minor_category,
            "version": version,
            "image_build_type": image_build_type,
            "image_build_region": image_build_region,
            "image_build_cluster": image_build_cluster,
            "Image_build_config": config_data,
            "resourcePool": resource_pool,
            "instances": instances_data,
        }

        resp = self._post(
            "/aiapi/v1/image-sync-server/register",
            body=maybe_transform(data, RegisterImageRequest),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=RegisterImageResponse
        )
        return resp.data

    def list(
            self,
            *,
            page: int = 1,
            pageSize: int = 15,
            minor_category: str | None = None,
            image_build_cluster: str | None = None,
            image_build_region: str | None = None,
            image_build_type: str | None = None,
            keyword: str | None = None,
            extra_headers: Headers | None = None,
            extra_query: Query | None = None,
            extra_body: Body | None = None,
            timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> ListResp:
        query: Query = {
            "page": page,
            "pageSize": pageSize,
            "filter.major_category":"siflow"
        }

        if minor_category is not None:
            query["filter.minor_category"] = minor_category
        if image_build_cluster is not None:
            query["filter.image_build_cluster"] = image_build_cluster
        if image_build_region is not None:
            query["filter.image_build_region"] = image_build_region
        if image_build_type is not None:
            query["filter.image_build_type"] = image_build_type
        if keyword is not None:
            query["filter.keyword"] = keyword

        resp = self._get(
            "/aiapi/v1/image-sync-server/images-management",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=query,
            ),
            cast_to=ListResp[ImageListResponse],
        )
        return resp

    def share(
            self,
            *,
            image_id: int = 1,
            is_show_all_users: Optional[bool] = None,
            users: Optional[List[str]] = None,
            extra_headers: Headers | None = None,
            extra_query: Query | None = None,
            extra_body: Body | None = None,
            timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> ImageShareResp:

        if extra_body is None:
            body = {}
            if is_show_all_users is not None:
                body["is_show_all_users"] = is_show_all_users
            if users is not None:
                body["users"] = users
            extra_body = body if body else None

        resp = self._put(
            f"/aiapi/v1/image-sync-server/images-management/{image_id}/share",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=ImageShareResp,
        )
        return resp




class ImagesWithRawResponse:
    def __init__(self, images: Images) -> None:
        self.create = to_raw_response_wrapper(images.create)
        self.list = to_raw_response_wrapper(images.list)
        self.share = to_raw_response_wrapper(images.share)
