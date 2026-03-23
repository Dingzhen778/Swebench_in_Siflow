from __future__ import annotations

from pydantic import Field
from typing import List, Optional

from .._models import BaseModel
from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven


__all__ = ["Model"]

# type ModelPVC struct {
# 	Name string `json:"name"`
# 	Path string `json:"path"`
# }

# type ModelBrief struct {
# 	IsPreset    bool     `json:"isPreset"`
# 	IsDeployed  bool     `json:"isDeployed"`
# 	UUID        string   `json:"uuid"`
# 	Cluster     string   `json:"cluster"`
# 	Name        string   `json:"name"`
# 	Type        string   `json:"type"`
# 	Version     string   `json:"version"`
# 	PVC         ModelPVC `json:"pvc"`
# 	Description string   `json:"description"`
# 	Tags        []string `json:"tags"`
# 	CreateTime  string   `json:"createTime"`
# 	UpdateTime  string   `json:"updateTime"`
# }


class ModelVolume(BaseModel):
    name: str
    """pvc name of volume where model placed"""

    path: str
    """relative path of model in volume"""


class Model(BaseModel):
    uuid: str
    """uuid of models"""

    name: str
    """model name"""

    cluster: str
    """cluster where model placed"""

    type: str
    """model type"""

    is_preset: Optional[bool] = Field(alias="isPreset")
    """whether model is preset"""

    is_deployed: Optional[bool] = Field(alias="isDeployed")
    """whether model has been deployed"""

    version: str
    """model version"""

    pvc: ModelVolume
    """pvc info of volume where model placed"""

    description: str
    """description of model"""

    tags: List[str]
    """model tags"""

    create_time: str = Field(alias="createTime")
    """model create time"""

    update_time: str = Field(alias="updateTime")
    """model update time"""
