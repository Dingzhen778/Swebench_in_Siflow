from pydantic import Field
from .._models import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class ImageBuildConfigArgRequest(BaseModel):
    key: str
    value: str
    hidden: bool


class ImageBuildConfigRequest(BaseModel):
    commit_id: Optional[str] = Field(None, alias="commit_id")
    build_method: Optional[str] = Field(None, alias="build_method")
    basic_image_type: Optional[str] = Field(None, alias="basic_image_type")
    basic_image_url: Optional[str] = Field(None, alias="basic_image_url")
    pip: Optional[str] = Field(None, alias="pip")
    apt: Optional[str] = Field(None, alias="apt")
    dockerfile_content: Optional[str] = Field(None, alias="dockerfile_content")
    dockerfile_path: Optional[str] = Field(None, alias="dockerfile_path")
    docker_hub_url: Optional[str] = Field(None, alias="docker_hub_url")
    description: Optional[str] = Field(None, alias="description")
    dockerfile_arg: Optional[List[ImageBuildConfigArgRequest]] = Field(default=None, alias="dockerfile_arg")


class InstanceRequest(BaseModel):
    name: str = Field(..., description="实例名称")
    countPerPod: int = Field(..., description="每个Pod的实例数量")


class RegisterImageRequest(BaseModel):
    name: str = Field(..., description="镜像名称")
    major_category: Optional[str] = Field(None, alias="major_category", description="镜像大类别")
    minor_category: Optional[str] = Field(None, alias="minor_category", description="镜像小类别")
    version: str = Field(..., description="镜像版本")
    image_build_type: Optional[str] = Field(None, alias="image_build_type", description="镜像build类型，preset/custom")
    image_build_region: Optional[str] = Field(None, alias="image_build_region", description="镜像build region")
    image_build_cluster: Optional[str] = Field(None, alias="image_build_cluster", description="镜像build cluster")
    image_build_config: Optional[ImageBuildConfigRequest] = Field(None, alias="Image_build_config")
    resource_pool: Optional[str] = Field(None, alias="resourcePool", description="资源池")
    instances: Optional[List[InstanceRequest]] = Field(None, alias="instances", description="实例配置列表")


class ImageListResponse(BaseModel):
    id: int
    name: str
    version: str
    major_category: Optional[str]
    minor_category: Optional[str]
    image_build_type: Optional[str]
    image_build_status: Optional[str]
    image_build_size: Optional[str]
    image_build_message: Optional[str]
    description: Optional[str]
    status: Optional[str]

    is_builtin: bool
    is_deleted: bool
    is_show_all_users: bool
    is_show_in_all_clusters: bool

    cluster_images_url: List[str]
    show_clusters: List[str]
    no_show_clusters: List[str]
    users: List[str]

    owner: str
    created_at: str  # or datetime if you want automatic parsing
    updated_at: str  # or datetime


class RegisterImageResponse(BaseModel):
    id: int
    name: str
    major_category: str
    minor_category: str
    version: str
    owner: str
    is_show_all_users: bool
    users: Optional[str]
    status: str
    is_show_in_all_clusters: bool
    description: Optional[str]
    show_clusters: Optional[str]
    is_deleted: bool
    image_build_type: Optional[str]
    image_build_size: Optional[str]
    image_build_status: Optional[str]
    image_build_org_name: Optional[str]
    image_build_job_name: Optional[str]
    image_build_region: Optional[str]
    image_build_cluster: Optional[str]
    image_build_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    instances: Optional[List[InstanceRequest]]
    resource_pool: Optional[str]


class ImageShareReq(BaseModel):
    id: int
    is_show_all_users: bool
    users: List[str]


class ImageShareResp(BaseModel):
    status: bool
    """response status"""

    msg: str
    """message of response status"""
