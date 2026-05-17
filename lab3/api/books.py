from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.book import BookIn, BookOut, ReadStatus, BookPageOut
from services import book_service
from database import get_db

router = APIRouter(prefix="/books", tags=["books"])


@router.get("/", response_model=BookPageOut)
async def list_books(
    status: Optional[ReadStatus] = Query(None),
    author: Optional[str] = Query(None, description="Partial, case-insensitive"),
    sort_by: Optional[str] = Query(None, pattern="^(title|year)$"),
    cursor: Optional[str] = Query(None, description="Token from previous response"),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    try:
        entries, next_cur = await book_service.list_books(
            db, status=status, author=author, sort_by=sort_by, cursor=cursor, limit=limit
        )
    except ValueError:
        raise HTTPException(status_code=422, detail="Cursor token is not valid")
    return BookPageOut(items=entries, next_cursor=next_cur, limit=limit)


@router.get("/{uid}", response_model=BookOut)
async def get_book(uid: str, db: AsyncSession = Depends(get_db)):
    entry = await book_service.get_entry(db, uid)
    if entry is None:
        raise HTTPException(status_code=404, detail="Not found")
    return entry


@router.post("/", response_model=BookOut, status_code=201)
async def add_book(payload: BookIn, db: AsyncSession = Depends(get_db)):
    return await book_service.register_book(db, payload)


@router.delete("/{uid}", status_code=204)
async def delete_book(uid: str, db: AsyncSession = Depends(get_db)):
    await book_service.drop_book(db, uid)
