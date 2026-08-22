from pydantic import BaseModel
from typing import Any


class PaginationParams(BaseModel):
    skip: int = 0
    limit: int = 50


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    skip: int
    limit: int
