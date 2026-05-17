import asyncio
import os

import database
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

_TEST_DB = "test_library.db"
_test_engine = create_async_engine(f"sqlite+aiosqlite:///{_TEST_DB}")
_TestSession = async_sessionmaker(_test_engine, expire_on_commit=False)
database.engine = _test_engine

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from main import app
from database import get_db, Base
from models.book import Book
from models.user import User
from services import auth_service


async def _override_get_db():
    async with _TestSession() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(scope="session", autouse=True)
def client():
    if os.path.exists(_TEST_DB):
        os.remove(_TEST_DB)
    with TestClient(app) as c:
        yield c
    if os.path.exists(_TEST_DB):
        os.remove(_TEST_DB)


@pytest.fixture(autouse=True)
def clean_db(client):
    yield
    asyncio.run(_wipe())
    auth_service.clear_refresh_tokens()


async def _wipe():
    async with _TestSession() as session:
        await session.execute(delete(Book))
        await session.execute(delete(User))
        await session.commit()


ALICE = {"username": "alice", "password": "alice123"}
BOB = {"username": "bob", "password": "bob456"}
FIXTURE = {
    "title": "Kobzar", "author": "Taras Shevchenko",
    "year": 1840, "pages": 312, "status": "free",
}


def _signup_and_login(client, creds: dict) -> dict:
    client.post("/auth/register", json=creds)
    resp = client.post("/auth/login", json=creds)
    return resp.json()


@pytest.fixture
def alice_tokens(client):
    return _signup_and_login(client, ALICE)


@pytest.fixture
def bob_tokens(client):
    return _signup_and_login(client, BOB)


@pytest.fixture
def alice_headers(alice_tokens):
    return {"Authorization": f"Bearer {alice_tokens['access_token']}"}


@pytest.fixture
def bob_headers(bob_tokens):
    return {"Authorization": f"Bearer {bob_tokens['access_token']}"}
