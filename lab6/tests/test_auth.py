from fastapi.testclient import TestClient

ALICE = {"username": "alice", "password": "alice123"}


# ── POST /auth/register ───────────────────────────────────────────────────────

def test_register_201(client: TestClient):
    assert client.post("/auth/register", json=ALICE).status_code == 201


def test_register_returns_user(client: TestClient):
    data = client.post("/auth/register", json=ALICE).json()
    assert data["username"] == ALICE["username"]
    assert data["is_active"] is True
    assert "id" in data
    assert "password" not in data
    assert "role" not in data


def test_register_duplicate_409(client: TestClient):
    client.post("/auth/register", json=ALICE)
    assert client.post("/auth/register", json=ALICE).status_code == 409


def test_register_short_username_422(client: TestClient):
    assert client.post("/auth/register", json={**ALICE, "username": "ab"}).status_code == 422


def test_register_short_password_422(client: TestClient):
    assert client.post("/auth/register", json={**ALICE, "password": "12345"}).status_code == 422


# ── POST /auth/login ──────────────────────────────────────────────────────────

def test_login_200(client: TestClient):
    client.post("/auth/register", json=ALICE)
    assert client.post("/auth/login", json=ALICE).status_code == 200


def test_login_returns_tokens(client: TestClient):
    client.post("/auth/register", json=ALICE)
    data = client.post("/auth/login", json=ALICE).json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password_401(client: TestClient):
    client.post("/auth/register", json=ALICE)
    assert client.post("/auth/login", json={**ALICE, "password": "wrongpass"}).status_code == 401


def test_login_unknown_user_401(client: TestClient):
    assert client.post("/auth/login", json={"username": "nobody", "password": "pass123"}).status_code == 401


def test_login_two_tokens_differ(client: TestClient):
    client.post("/auth/register", json=ALICE)
    t1 = client.post("/auth/login", json=ALICE).json()["access_token"]
    t2 = client.post("/auth/login", json=ALICE).json()["access_token"]
    assert t1 != t2


# ── POST /auth/refresh ────────────────────────────────────────────────────────

def test_refresh_returns_new_pair(client: TestClient, alice_tokens):
    old_access = alice_tokens["access_token"]
    data = client.post("/auth/refresh", json={"refresh_token": alice_tokens["refresh_token"]}).json()
    assert "access_token" in data
    assert data["access_token"] != old_access


def test_refresh_rotates_token(client: TestClient, alice_tokens):
    old_refresh = alice_tokens["refresh_token"]
    new_tokens = client.post("/auth/refresh", json={"refresh_token": old_refresh}).json()
    assert client.post("/auth/refresh", json={"refresh_token": old_refresh}).status_code == 401
    assert client.post("/auth/refresh", json={"refresh_token": new_tokens["refresh_token"]}).status_code == 200


def test_refresh_new_token_works(client: TestClient, alice_tokens):
    new_tokens = client.post("/auth/refresh", json={"refresh_token": alice_tokens["refresh_token"]}).json()
    headers = {"Authorization": f"Bearer {new_tokens['access_token']}"}
    assert client.get("/books/", headers=headers).status_code == 200


def test_refresh_invalid_401(client: TestClient):
    assert client.post("/auth/refresh", json={"refresh_token": "not.valid.token"}).status_code == 401


# ── POST /auth/logout ─────────────────────────────────────────────────────────

def test_logout_200(client: TestClient, alice_tokens):
    assert client.post("/auth/logout", json={"refresh_token": alice_tokens["refresh_token"]}).status_code == 200


def test_logout_invalidates_token(client: TestClient, alice_tokens):
    client.post("/auth/logout", json={"refresh_token": alice_tokens["refresh_token"]})
    assert client.post("/auth/refresh", json={"refresh_token": alice_tokens["refresh_token"]}).status_code == 401
