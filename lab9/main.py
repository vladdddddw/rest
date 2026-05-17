from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI
from sqlalchemy import func, select

import database
from api.books import router as books_router
from models.book import Book

_TITLES = [
    "Kobzar", "Eneyida", "Lisova pisnia", "Tini zabutykh predkiv",
    "Intermezzo", "Zemlia", "Pryimachka", "Bur'yan", "Vovchykha",
    "Kaidasheva simia", "Chorna Rada", "Fata Morgana",
]
_AUTHORS = [
    "Taras Shevchenko", "Ivan Kotlyarevsky", "Lesia Ukrainka",
    "Mykhailo Kotsiubynsky", "Ivan Nechui-Levytsky", "Panas Myrny",
    "Panteleimon Kulish", "Olha Kobylianska",
]
_PAGES = [120, 200, 312, 440, 88, 256, 180, 350, 95, 280, 165, 420]


async def _seed_books() -> None:
    async with database.AsyncSessionLocal() as session:
        count = (await session.execute(
            select(func.count()).select_from(Book)
        )).scalar()
        if count > 0:
            return
        entries = [
            Book(
                id=str(uuid4()),
                title=f"{_TITLES[i % len(_TITLES)]} {i + 1}",
                author=_AUTHORS[i % len(_AUTHORS)],
                year=1800 + (i % 200),
                pages=_PAGES[i % len(_PAGES)],
                summary=f"Entry #{i + 1}",
                status="free" if i % 4 != 0 else "on_loan",
            )
            for i in range(200)
        ]
        session.add_all(entries)
        await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with database.engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)
    await _seed_books()
    yield


app = FastAPI(
    title="Book Catalog API — Load Test",
    description="GET /books/ endpoint for Locust load testing",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(books_router)


@app.get("/")
async def index():
    return {"message": "Book Catalog API"}
