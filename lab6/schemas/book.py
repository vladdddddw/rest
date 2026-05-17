from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class ReadStatus(str, Enum):
    FREE = "free"
    ON_LOAN = "on_loan"


class BookIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    year: int = Field(..., ge=1000, le=2100)
    pages: Optional[int] = Field(None, ge=1, le=10000)
    summary: Optional[str] = Field(None, max_length=1000)
    status: ReadStatus = ReadStatus.FREE


class BookOut(BaseModel):
    id: str
    title: str
    author: str
    year: int
    pages: Optional[int] = None
    summary: Optional[str] = None
    status: ReadStatus

    model_config = {"from_attributes": True}


class BookListOut(BaseModel):
    items: List[BookOut]
    total: int
    limit: int
    offset: int
