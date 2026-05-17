from fastapi.testclient import TestClient

FIXTURE = {
    "title": "Kobzar", "author": "Taras Shevchenko",
    "year": 1840, "pages": 312, "status": "free",
}


# ── No token — public GET ─────────────────────────────────────────────────────

def test_get_list_no_auth_200(client: TestClient):
    assert client.get("/books/").status_code == 200


def test_get_single_no_auth_200(client: TestClient, alice_headers):
    uid = client.post("/books/", json=FIXTURE, headers=alice_headers).json()["id"]
    assert client.get(f"/books/{uid}").status_code == 200


# ── Auth required for writes ──────────────────────────────────────────────────

def test_post_no_token_401(client: TestClient):
    assert client.post("/books/", json=FIXTURE).status_code == 401


def test_delete_no_token_401(client: TestClient, alice_headers):
    uid = client.post("/books/", json=FIXTURE, headers=alice_headers).json()["id"]
    assert client.delete(f"/books/{uid}").status_code == 401


def test_invalid_token_401(client: TestClient):
    headers = {"Authorization": "Bearer not.valid.token"}
    assert client.post("/books/", json=FIXTURE, headers=headers).status_code == 401


# ── Authenticated user can do full CRUD ──────────────────────────────────────

def test_post_with_auth_201(client: TestClient, alice_headers):
    assert client.post("/books/", json=FIXTURE, headers=alice_headers).status_code == 201


def test_post_fields(client: TestClient, alice_headers):
    data = client.post("/books/", json=FIXTURE, headers=alice_headers).json()
    assert data["title"] == FIXTURE["title"]
    assert data["pages"] == FIXTURE["pages"]
    assert data["status"] == "free"


def test_post_unique_ids(client: TestClient, alice_headers):
    a = client.post("/books/", json=FIXTURE, headers=alice_headers).json()["id"]
    b = client.post("/books/", json=FIXTURE, headers=alice_headers).json()["id"]
    assert a != b


def test_any_user_can_post(client: TestClient, bob_headers):
    assert client.post("/books/", json=FIXTURE, headers=bob_headers).status_code == 201


def test_get_list_with_auth_200(client: TestClient, alice_headers):
    assert client.get("/books/", headers=alice_headers).status_code == 200


def test_get_list_structure(client: TestClient, alice_headers):
    client.post("/books/", json=FIXTURE, headers=alice_headers)
    data = client.get("/books/").json()
    assert all(k in data for k in ("items", "total", "limit", "offset"))


def test_filter_status_free(client: TestClient, alice_headers):
    client.post("/books/", json={**FIXTURE, "status": "free"}, headers=alice_headers)
    client.post("/books/", json={**FIXTURE, "title": "B", "status": "on_loan"}, headers=alice_headers)
    data = client.get("/books/?status=free").json()
    assert data["total"] == 1 and data["items"][0]["status"] == "free"


def test_filter_status_on_loan(client: TestClient, alice_headers):
    client.post("/books/", json={**FIXTURE, "status": "on_loan"}, headers=alice_headers)
    client.post("/books/", json={**FIXTURE, "title": "B", "status": "free"}, headers=alice_headers)
    data = client.get("/books/?status=on_loan").json()
    assert data["total"] == 1


def test_pagination(client: TestClient, alice_headers):
    for i in range(5):
        client.post("/books/", json={**FIXTURE, "title": f"Book{i}"}, headers=alice_headers)
    data = client.get("/books/?limit=3").json()
    assert len(data["items"]) == 3 and data["total"] == 5


def test_get_single_200(client: TestClient, alice_headers):
    uid = client.post("/books/", json=FIXTURE, headers=alice_headers).json()["id"]
    assert client.get(f"/books/{uid}").status_code == 200


def test_get_single_404(client: TestClient):
    assert client.get("/books/00000000-0000-0000-0000-000000000000").status_code == 404


def test_delete_204(client: TestClient, alice_headers):
    uid = client.post("/books/", json=FIXTURE, headers=alice_headers).json()["id"]
    assert client.delete(f"/books/{uid}", headers=alice_headers).status_code == 204


def test_delete_removes(client: TestClient, alice_headers):
    uid = client.post("/books/", json=FIXTURE, headers=alice_headers).json()["id"]
    client.delete(f"/books/{uid}", headers=alice_headers)
    assert client.get(f"/books/{uid}").status_code == 404


def test_delete_idempotent(client: TestClient, alice_headers):
    uid = client.post("/books/", json=FIXTURE, headers=alice_headers).json()["id"]
    client.delete(f"/books/{uid}", headers=alice_headers)
    assert client.delete(f"/books/{uid}", headers=alice_headers).status_code == 204


def test_post_missing_title_422(client: TestClient, alice_headers):
    book = {k: v for k, v in FIXTURE.items() if k != "title"}
    assert client.post("/books/", json=book, headers=alice_headers).status_code == 422


def test_post_invalid_status_422(client: TestClient, alice_headers):
    assert client.post("/books/", json={**FIXTURE, "status": "broken"}, headers=alice_headers).status_code == 422
