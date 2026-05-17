from typing import Optional
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from models.book import Book


async def fetch_all(
    db: AsyncSession,
    status: Optional[str] = None,
    author: Optional[str] = None,
    pages_min: Optional[int] = None,
    sort_by: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
) -> tuple[list[Book], int]:
    q = select(Book)
    cq = select(func.count()).select_from(Book)

    if status is not None:
        q = q.where(Book.status == status)
        cq = cq.where(Book.status == status)
    if author is not None:
        q = q.where(Book.author.ilike(f"%{author}%"))
        cq = cq.where(Book.author.ilike(f"%{author}%"))
    if pages_min is not None:
        q = q.where(Book.pages >= pages_min)
        cq = cq.where(Book.pages >= pages_min)

    if sort_by == "title":
        q = q.order_by(Book.title)
    elif sort_by == "year":
        q = q.order_by(Book.year)

    q = q.limit(limit).offset(offset)
    rows = await db.execute(q)
    count = await db.execute(cq)
    return list(rows.scalars().all()), count.scalar()


async def find_by_id(db: AsyncSession, uid: str) -> Optional[Book]:
    result = await db.execute(select(Book).where(Book.id == uid))
    return result.scalar_one_or_none()


async def save(db: AsyncSession, data: dict) -> Book:
    entry = Book(**data)
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def remove(db: AsyncSession, uid: str) -> bool:
    result = await db.execute(delete(Book).where(Book.id == uid))
    await db.commit()
    return result.rowcount > 0
