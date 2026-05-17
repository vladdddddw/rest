from typing import List, Dict, Optional
from models.book import library_store


async def fetch_all() -> List[Dict]:
    return list(library_store)


async def find_by_id(uid: str) -> Optional[Dict]:
    return next((e for e in library_store if e["id"] == uid), None)


async def save(entry: Dict) -> Dict:
    library_store.append(entry)
    return entry


async def remove(uid: str) -> bool:
    for i, e in enumerate(library_store):
        if e["id"] == uid:
            library_store.pop(i)
            return True
    return False
