import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.book import BookIn, ReadStatus
from repository import book_repository
from models.book import Book


async def list_books(
    db: AsyncSession,
    status: Optional[ReadStatus] = None,
    author: Optional[str] = None,
    sort_by: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
) -> tuple[list[Book], int]:
    return await book_repository.fetch_all(
        db,
        status=status.value if status else None,
        author=author,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
    )


async def get_entry(db: AsyncSession, uid: str) -> Optional[Book]:
    return await book_repository.find_by_id(db, uid)


async def register_book(db: AsyncSession, payload: BookIn) -> Book:
    data = {
        "id": str(uuid.uuid4()),
        "title": payload.title,
        "author": payload.author,
        "year": payload.year,
        "pages": payload.pages,
        "summary": payload.summary,
        "status": payload.status.value,
    }
    return await book_repository.save(db, data)


async def drop_book(db: AsyncSession, uid: str) -> bool:
    return await book_repository.remove(db, uid)
