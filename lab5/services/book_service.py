import uuid
from typing import Optional
from repository import book_repository


def list_books(
    status: Optional[str] = None,
    author: Optional[str] = None,
    pages_min: Optional[int] = None,
    sort_by: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
) -> tuple[list[dict], int]:
    return book_repository.fetch_all(
        status=status, author=author, pages_min=pages_min,
        sort_by=sort_by, limit=limit, offset=offset,
    )


def get_entry(uid: str) -> Optional[dict]:
    return book_repository.find_by_id(uid)


def register_book(data: dict) -> dict:
    data["id"] = str(uuid.uuid4())
    return book_repository.save(data)


def drop_book(uid: str) -> bool:
    return book_repository.remove(uid)
