import uuid
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.book import BOOKS_COLLECTION


def _doc_to_dict(doc: dict) -> dict:
    out = dict(doc)
    out["id"] = str(out.pop("_id"))
    return out


async def fetch_all(
    db: AsyncIOMotorDatabase,
    status: Optional[str] = None,
    author: Optional[str] = None,
    pages_min: Optional[int] = None,
    sort_by: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
) -> tuple[list[dict], int]:
    flt: dict = {}
    if status is not None:
        flt["status"] = status
    if author is not None:
        flt["author"] = {"$regex": author, "$options": "i"}
    if pages_min is not None:
        flt["pages"] = {"$gte": pages_min}

    ordering: list = [("_id", 1)]
    if sort_by == "title":
        ordering = [("title", 1), ("_id", 1)]
    elif sort_by == "year":
        ordering = [("year", 1), ("_id", 1)]

    col = db[BOOKS_COLLECTION]
    total = await col.count_documents(flt)
    docs = await col.find(flt).sort(ordering).skip(offset).limit(limit).to_list(length=limit)
    return [_doc_to_dict(d) for d in docs], total


async def find_by_id(db: AsyncIOMotorDatabase, uid: str) -> Optional[dict]:
    doc = await db[BOOKS_COLLECTION].find_one({"_id": uid})
    return _doc_to_dict(doc) if doc else None


async def save(db: AsyncIOMotorDatabase, data: dict) -> dict:
    uid = str(uuid.uuid4())
    await db[BOOKS_COLLECTION].insert_one({"_id": uid, **data})
    return {"id": uid, **data}


async def remove(db: AsyncIOMotorDatabase, uid: str) -> bool:
    result = await db[BOOKS_COLLECTION].delete_one({"_id": uid})
    return result.deleted_count > 0
