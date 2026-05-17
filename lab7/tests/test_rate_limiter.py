import asyncio
import time
import jwt
import pytest
from fastapi.testclient import TestClient


async def _fill_key(redis, key: str, count: int) -> None:
    ts = int(time.time())
    entries = {f"req:{i}": float(ts - i) for i in range(count)}
    await redis.zadd(key, entries)


# ── Anonymous (limit = 3) ─────────────────────────────────────────────────────

def test_anon_first_request_not_429(client: TestClient):
    resp = client.post("/auth/login", json={"username": "nobody", "password": "nobody"})
    assert resp.status_code != 429


def test_anon_at_limit_returns_429(client: TestClient, fake_redis):
    asyncio.run(_fill_key(fake_redis, "rl:testclient", 3))
    resp = client.post("/auth/login", json={"username": "x", "password": "x"})
    assert resp.status_code == 429


def test_anon_below_limit_not_429(client: TestClient, fake_redis):
    asyncio.run(_fill_key(fake_redis, "rl:testclient", 2))
    resp = client.post("/auth/login", json={"username": "x", "password": "x"})
    assert resp.status_code != 429


def test_anon_429_has_detail(client: TestClient, fake_redis):
    asyncio.run(_fill_key(fake_redis, "rl:testclient", 3))
    resp = client.post("/auth/login", json={"username": "x", "password": "x"})
    assert resp.status_code == 429
    assert "detail" in resp.json()


def test_anon_429_has_retry_after(client: TestClient, fake_redis):
    asyncio.run(_fill_key(fake_redis, "rl:testclient", 3))
    resp = client.post("/auth/login", json={"username": "x", "password": "x"})
    assert resp.status_code == 429
    assert "retry-after" in {h.lower() for h in resp.headers}


def test_anon_limit_is_3(client: TestClient, fake_redis):
    for _ in range(3):
        assert client.post("/auth/login", json={"username": "x", "password": "x"}).status_code != 429
    assert client.post("/auth/login", json={"username": "x", "password": "x"}).status_code == 429


# ── Authenticated (limit = 15) ────────────────────────────────────────────────

def test_auth_first_request_200(client: TestClient, alice_headers):
    assert client.get("/books/", headers=alice_headers).status_code == 200


def test_auth_at_limit_returns_429(client: TestClient, alice_tokens, fake_redis):
    payload = jwt.decode(alice_tokens["access_token"], options={"verify_signature": False})
    user_id = payload["uid"]
    asyncio.run(_fill_key(fake_redis, f"rl:{user_id}", 15))
    assert client.get("/books/", headers={"Authorization": f"Bearer {alice_tokens['access_token']}"}).status_code == 429


def test_auth_below_limit_not_429(client: TestClient, alice_tokens, fake_redis):
    payload = jwt.decode(alice_tokens["access_token"], options={"verify_signature": False})
    user_id = payload["uid"]
    asyncio.run(_fill_key(fake_redis, f"rl:{user_id}", 14))
    assert client.get("/books/", headers={"Authorization": f"Bearer {alice_tokens['access_token']}"}).status_code == 200


def test_auth_429_has_detail(client: TestClient, alice_tokens, fake_redis):
    payload = jwt.decode(alice_tokens["access_token"], options={"verify_signature": False})
    asyncio.run(_fill_key(fake_redis, f"rl:{payload['uid']}", 15))
    resp = client.get("/books/", headers={"Authorization": f"Bearer {alice_tokens['access_token']}"})
    assert resp.status_code == 429
    assert "detail" in resp.json()


def test_users_have_separate_counters(client: TestClient, alice_tokens, bob_tokens, fake_redis):
    alice_id = jwt.decode(alice_tokens["access_token"], options={"verify_signature": False})["uid"]
    asyncio.run(_fill_key(fake_redis, f"rl:{alice_id}", 15))
    assert client.get("/books/", headers={"Authorization": f"Bearer {alice_tokens['access_token']}"}).status_code == 429
    assert client.get("/books/", headers={"Authorization": f"Bearer {bob_tokens['access_token']}"}).status_code == 200


def test_counter_increments(client: TestClient, alice_headers, alice_tokens, fake_redis):
    uid = jwt.decode(alice_tokens["access_token"], options={"verify_signature": False})["uid"]
    key = f"rl:{uid}"

    async def _count():
        return await fake_redis.zcard(key)

    before = asyncio.run(_count())
    client.get("/books/", headers=alice_headers)
    assert asyncio.run(_count()) == before + 1


def test_auth_limit_is_15(client: TestClient, alice_tokens, fake_redis):
    headers = {"Authorization": f"Bearer {alice_tokens['access_token']}"}
    for _ in range(15):
        assert client.get("/books/", headers=headers).status_code == 200
    assert client.get("/books/", headers=headers).status_code == 429
