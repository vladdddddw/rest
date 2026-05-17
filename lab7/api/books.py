from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.book import BookIn, BookOut, ReadStatus, BookListOut
from services import book_service
from database import get_db
from core.dependencies import get_current_user
from core.rate_limiter import rate_limit

router = APIRouter(prefix="/books", tags=["books"])


@router.get("/", response_model=BookListOut)
async def list_books(
    status: Optional[ReadStatus] = Query(None),
    author: Optional[str] = Query(None),
    pages_min: Optional[int] = Query(None, ge=1),
    sort_by: Optional[str] = Query(None, pattern="^(title|year)$"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(rate_limit),
):
    records, total = await book_service.list_books(
        db, status=status, author=author, pages_min=pages_min,
        sort_by=sort_by, limit=limit, offset=offset,
    )
    return BookListOut(items=records, total=total, limit=limit, offset=offset)


@router.get("/{uid}", response_model=BookOut)
async def get_book(uid: str, db: AsyncSession = Depends(get_db), _rl: None = Depends(rate_limit)):
    entry = await book_service.get_entry(db, uid)
    if entry is None:
        raise HTTPException(status_code=404, detail="Not found")
    return entry


@router.post("/", response_model=BookOut, status_code=201)
async def add_book(
    payload: BookIn,
    db: AsyncSession = Depends(get_db),
    _auth: dict = Depends(get_current_user),
    _rl: None = Depends(rate_limit),
):
    return await book_service.register_book(db, payload)


@router.delete("/{uid}", status_code=204)
async def delete_book(
    uid: str,
    db: AsyncSession = Depends(get_db),
    _auth: dict = Depends(get_current_user),
    _rl: None = Depends(rate_limit),
):
    await book_service.drop_book(db, uid)
