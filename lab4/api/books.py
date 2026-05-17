from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from schemas.book import BookIn, BookOut, ReadStatus, BookListOut
from services import book_service
from database import get_database

router = APIRouter(prefix="/books", tags=["books"])


@router.get("/", response_model=BookListOut)
async def list_books(
    status: Optional[ReadStatus] = Query(None),
    author: Optional[str] = Query(None, description="Partial, case-insensitive"),
    pages_min: Optional[int] = Query(None, ge=1),
    sort_by: Optional[str] = Query(None, pattern="^(title|year)$"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    records, total = await book_service.list_books(
        db, status=status, author=author, pages_min=pages_min,
        sort_by=sort_by, limit=limit, offset=offset,
    )
    return BookListOut(items=records, total=total, limit=limit, offset=offset)


@router.get("/{uid}", response_model=BookOut)
async def get_book(uid: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    entry = await book_service.get_entry(db, uid)
    if entry is None:
        raise HTTPException(status_code=404, detail="Not found")
    return entry


@router.post("/", response_model=BookOut, status_code=201)
async def add_book(payload: BookIn, db: AsyncIOMotorDatabase = Depends(get_database)):
    return await book_service.register_book(db, payload)


@router.delete("/{uid}", status_code=204)
async def delete_book(uid: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    await book_service.drop_book(db, uid)
