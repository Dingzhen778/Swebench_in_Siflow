from __future__ import annotations

from typing import List
from datetime import datetime

from .._models import BaseModel
from .sieval_cases import CaseRead, CaseReadSimple


class DatasetRead(BaseModel):
    name: str
    description: str | None = None
    label_l1: str
    label_l2: str
    samples: int = 0

    created_at: datetime
    updated_at: datetime

    cases: List[CaseRead]


class DatasetReadSimple(BaseModel):
    id: int
    name: str
    label_l1: str | None = None
    label_l2: str | None = None
    samples: int

    created_at: datetime
    updated_at: datetime

    cases: List[CaseReadSimple]
