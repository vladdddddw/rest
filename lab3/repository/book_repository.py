import json
import base64
from typing import Optional
from sqlalchemy import select, delete, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from models.book import Book


def pack_cursor(data: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode()


def unpack_cursor(token: str) -> dict:
    try:
        result = json.loads(base64.urlsafe_b64decode(token.encode()).decode())
        if not isinstance(result, dict):
            raise ValueError
        return result
    except Exception:
        raise ValueError("Invalid cursor token")


async def fetch_page(
    db: AsyncSession,
    status: Optional[str] = None,
    author: Optional[str] = None,
    sort_by: Optional[str] = None,
    cursor: Optional[str] = None,
    limit: int = 10,
) -> tuple[list[Book], Optional[str]]:
    pos = unpack_cursor(cursor) if cursor else {}

    q = select(Book)

    if status is not None:
        q = q.where(Book.status == status)
    if author is not None:
        q = q.where(Book.author.ilike(f"%{author}%"))

    if sort_by == "title":
        if pos:
            q = q.where(or_(Book.title > pos.get("title", ""), and_(Book.title == pos.get("title", ""), Book.id > pos.get("id", ""))))
        q = q.order_by(Book.title, Book.id)
    elif sort_by == "year":
        if pos:
            q = q.where(or_(Book.year > pos.get("year", 0), and_(Book.year == pos.get("year", 0), Book.id > pos.get("id", ""))))
        q = q.order_by(Book.year, Book.id)
    else:
        if pos:
            q = q.where(Book.id > pos.get("id", ""))
        q = q.order_by(Book.id)

    rows = await db.execute(q.limit(limit + 1))
    entries = list(rows.scalars().all())

    has_more = len(entries) > limit
    if has_more:
        entries = entries[:limit]

    next_cur: Optional[str] = None
    if has_more and entries:
        last = entries[-1]
        if sort_by == "title":
            next_cur = pack_cursor({"title": last.title, "id": last.id})
        elif sort_by == "year":
            next_cur = pack_cursor({"year": last.year, "id": last.id})
        else:
            next_cur = pack_cursor({"id": last.id})

    return entries, next_cur


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
