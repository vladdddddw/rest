from typing import Optional
from models.book import library_store


def fetch_all(
    status: Optional[str] = None,
    author: Optional[str] = None,
    pages_min: Optional[int] = None,
    sort_by: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
) -> tuple[list[dict], int]:
    records = list(library_store)

    if status is not None:
        records = [r for r in records if r["status"] == status]
    if author is not None:
        records = [r for r in records if author.lower() in r["author"].lower()]
    if pages_min is not None:
        records = [r for r in records if r.get("pages") and r["pages"] >= pages_min]

    if sort_by == "title":
        records.sort(key=lambda r: r["title"].lower())
    elif sort_by == "year":
        records.sort(key=lambda r: r["year"])

    total = len(records)
    return records[offset: offset + limit], total


def find_by_id(uid: str) -> Optional[dict]:
    return next((r for r in library_store if r["id"] == uid), None)


def save(entry: dict) -> dict:
    library_store.append(entry)
    return entry


def remove(uid: str) -> bool:
    for i, r in enumerate(library_store):
        if r["id"] == uid:
            library_store.pop(i)
            return True
    return False
