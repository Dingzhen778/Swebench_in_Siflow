from __future__ import annotations

from pydantic import Field
from typing import Optional
# from typing_extensions import Literal, Annotated, TypedDict, Required

# from .._utils import PropertyInfo
from .._models import BaseModel


class DatasetVolume(BaseModel):
    name: str
    """dataset name"""

    version: Optional[str]
    """dataset version"""

    is_preset: bool = Field(alias="isPreset")
    """dataset type"""
    
    read_only: bool = Field(alias="readOnly")
    """read only"""

    pvc_name: str = Field(alias="pvc")
    """pvc name of dataset"""

    sub_path: Optional[str] = Field(alias="subPath")
    """relative path of dataset in volume"""
