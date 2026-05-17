from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from schemas.book import BookIn, BookOut, ReadStatus
from services import book_service

router = APIRouter(prefix="/books", tags=["books"])


@router.get("/", response_model=List[BookOut])
async def list_books(
    status: Optional[ReadStatus] = Query(None),
    author: Optional[str] = Query(None, description="Partial, case-insensitive"),
    pages_min: Optional[int] = Query(None, ge=1, description="Minimum page count"),
    sort_by: Optional[str] = Query(None, pattern="^(title|year)$"),
):
    return await book_service.list_books(
        status=status, author=author, pages_min=pages_min, sort_by=sort_by
    )


@router.get("/{uid}", response_model=BookOut)
async def get_book(uid: str):
    entry = await book_service.get_entry(uid)
    if entry is None:
        raise HTTPException(status_code=404, detail="Not found")
    return entry


@router.post("/", response_model=BookOut, status_code=201)
async def add_book(payload: BookIn):
    return await book_service.register_book(payload)


@router.delete("/{uid}", status_code=204)
async def delete_book(uid: str):
    await book_service.drop_book(uid)
