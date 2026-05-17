import uuid
from typing import List, Dict, Optional
from schemas.book import BookIn, ReadStatus
from repository import book_repository


async def list_books(
    status: Optional[ReadStatus] = None,
    author: Optional[str] = None,
    pages_min: Optional[int] = None,
    sort_by: Optional[str] = None,
) -> List[Dict]:
    records = await book_repository.fetch_all()

    if status is not None:
        records = [r for r in records if r["status"] == status.value]
    if author is not None:
        records = [r for r in records if author.lower() in r["author"].lower()]
    if pages_min is not None:
        records = [r for r in records if r.get("pages") and r["pages"] >= pages_min]

    if sort_by == "title":
        records.sort(key=lambda r: r["title"].lower())
    elif sort_by == "year":
        records.sort(key=lambda r: r["year"])

    return records


async def get_entry(uid: str) -> Optional[Dict]:
    return await book_repository.find_by_id(uid)


async def register_book(payload: BookIn) -> Dict:
    entry = {"id": str(uuid.uuid4()), **payload.model_dump()}
    return await book_repository.save(entry)


async def drop_book(uid: str) -> None:
    await book_repository.remove(uid)
