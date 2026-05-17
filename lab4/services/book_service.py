from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from schemas.book import BookIn, ReadStatus
from repository import book_repository


async def list_books(
    db: AsyncIOMotorDatabase,
    status: Optional[ReadStatus] = None,
    author: Optional[str] = None,
    pages_min: Optional[int] = None,
    sort_by: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
) -> tuple[list[dict], int]:
    return await book_repository.fetch_all(
        db,
        status=status.value if status else None,
        author=author,
        pages_min=pages_min,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
    )


async def get_entry(db: AsyncIOMotorDatabase, uid: str) -> Optional[dict]:
    return await book_repository.find_by_id(db, uid)


async def register_book(db: AsyncIOMotorDatabase, payload: BookIn) -> dict:
    data = {
        "title": payload.title,
        "author": payload.author,
        "year": payload.year,
        "pages": payload.pages,
        "summary": payload.summary,
        "status": payload.status.value,
    }
    return await book_repository.save(db, data)


async def drop_book(db: AsyncIOMotorDatabase, uid: str) -> bool:
    return await book_repository.remove(db, uid)
