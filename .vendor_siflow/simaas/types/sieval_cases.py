from __future__ import annotations

from typing import Literal
from datetime import datetime

from .._models import BaseModel


class CaseRead(BaseModel):
    id: int
    name: str
    mode: Literal["gen", "ppl"] = "gen"
    shots: int = 0
    judge: bool = False
    sandbox: bool = False

    created_at: datetime
    updated_at: datetime

    dataset_id: int


class CaseReadSimple(BaseModel):
    id: int
    name: str
    mode: Literal["gen", "ppl"] = "gen"
    shots: int = 0
    judge: bool = False
    sandbox: bool = False

    task_name: str | None
