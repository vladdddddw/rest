from fastapi.testclient import TestClient

ALICE = {"username": "alice", "password": "alice123"}


def test_register_201(client: TestClient):
    assert client.post("/auth/register", json=ALICE).status_code == 201


def test_register_no_role_in_response(client: TestClient):
    data = client.post("/auth/register", json=ALICE).json()
    assert data["username"] == ALICE["username"]
    assert "role" not in data
    assert "password" not in data


def test_register_duplicate_409(client: TestClient):
    client.post("/auth/register", json=ALICE)
    assert client.post("/auth/register", json=ALICE).status_code == 409


def test_register_short_username_422(client: TestClient):
    assert client.post("/auth/register", json={**ALICE, "username": "ab"}).status_code == 422


def test_login_200(client: TestClient):
    client.post("/auth/register", json=ALICE)
    assert client.post("/auth/login", json=ALICE).status_code == 200


def test_login_returns_tokens(client: TestClient):
    client.post("/auth/register", json=ALICE)
    data = client.post("/auth/login", json=ALICE).json()
    assert "access_token" in data and "refresh_token" in data


def test_login_wrong_password_401(client: TestClient):
    client.post("/auth/register", json=ALICE)
    assert client.post("/auth/login", json={**ALICE, "password": "wrong"}).status_code == 401


def test_login_unknown_user_401(client: TestClient):
    assert client.post("/auth/login", json={"username": "ghost", "password": "pass123"}).status_code == 401


def test_refresh_returns_new_tokens(client: TestClient, alice_tokens):
    old = alice_tokens["access_token"]
    new = client.post("/auth/refresh", json={"refresh_token": alice_tokens["refresh_token"]}).json()
    assert new["access_token"] != old


def test_refresh_rotates(client: TestClient, alice_tokens):
    old_rt = alice_tokens["refresh_token"]
    new_tokens = client.post("/auth/refresh", json={"refresh_token": old_rt}).json()
    assert client.post("/auth/refresh", json={"refresh_token": old_rt}).status_code == 401
    assert client.post("/auth/refresh", json={"refresh_token": new_tokens["refresh_token"]}).status_code == 200


def test_refresh_invalid_401(client: TestClient):
    assert client.post("/auth/refresh", json={"refresh_token": "bad.token"}).status_code == 401


def test_logout_200(client: TestClient, alice_tokens):
    assert client.post("/auth/logout", json={"refresh_token": alice_tokens["refresh_token"]}).status_code == 200


def test_logout_invalidates(client: TestClient, alice_tokens):
    client.post("/auth/logout", json={"refresh_token": alice_tokens["refresh_token"]})
    assert client.post("/auth/refresh", json={"refresh_token": alice_tokens["refresh_token"]}).status_code == 401
