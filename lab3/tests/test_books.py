from fastapi.testclient import TestClient

FIXTURE = {
    "title": "Kobzar",
    "author": "Taras Shevchenko",
    "year": 1840,
    "pages": 312,
    "summary": "Klasychna zbirka",
    "status": "free",
}


# ── POST ──────────────────────────────────────────────────────────────────────

def test_post_201(client: TestClient):
    assert client.post("/books/", json=FIXTURE).status_code == 201


def test_post_fields(client: TestClient):
    data = client.post("/books/", json=FIXTURE).json()
    assert data["title"] == FIXTURE["title"]
    assert data["pages"] == FIXTURE["pages"]
    assert data["status"] == "free"


def test_post_unique_ids(client: TestClient):
    a = client.post("/books/", json=FIXTURE).json()
    b = client.post("/books/", json=FIXTURE).json()
    assert a["id"] != b["id"]


def test_post_default_free(client: TestClient):
    book = {k: v for k, v in FIXTURE.items() if k != "status"}
    assert client.post("/books/", json=book).json()["status"] == "free"


def test_post_on_loan(client: TestClient):
    assert client.post("/books/", json={**FIXTURE, "status": "on_loan"}).json()["status"] == "on_loan"


def test_post_no_pages_none(client: TestClient):
    book = {k: v for k, v in FIXTURE.items() if k != "pages"}
    assert client.post("/books/", json=book).json()["pages"] is None


def test_post_missing_title_422(client: TestClient):
    assert client.post("/books/", json={k: v for k, v in FIXTURE.items() if k != "title"}).status_code == 422


def test_post_missing_author_422(client: TestClient):
    assert client.post("/books/", json={k: v for k, v in FIXTURE.items() if k != "author"}).status_code == 422


def test_post_missing_year_422(client: TestClient):
    assert client.post("/books/", json={k: v for k, v in FIXTURE.items() if k != "year"}).status_code == 422


def test_post_year_low_422(client: TestClient):
    assert client.post("/books/", json={**FIXTURE, "year": 999}).status_code == 422


def test_post_invalid_status_422(client: TestClient):
    assert client.post("/books/", json={**FIXTURE, "status": "broken"}).status_code == 422


# ── GET list (cursor pagination) ──────────────────────────────────────────────

def test_list_empty(client: TestClient):
    data = client.get("/books/").json()
    assert data["items"] == [] and data["next_cursor"] is None


def test_list_returns_items(client: TestClient):
    for t in ["Kobzar", "Eneyida", "Lisova Pisnya"]:
        client.post("/books/", json={**FIXTURE, "title": t})
    data = client.get("/books/").json()
    assert len(data["items"]) == 3


def test_cursor_pagination_first_page(client: TestClient):
    for i in range(5):
        client.post("/books/", json={**FIXTURE, "title": f"Book{i:02d}"})
    data = client.get("/books/?limit=3").json()
    assert len(data["items"]) == 3
    assert data["next_cursor"] is not None


def test_cursor_pagination_second_page(client: TestClient):
    for i in range(5):
        client.post("/books/", json={**FIXTURE, "title": f"Book{i:02d}"})
    page1 = client.get("/books/?sort_by=title&limit=3").json()
    cursor = page1["next_cursor"]
    page2 = client.get(f"/books/?sort_by=title&limit=3&cursor={cursor}").json()
    assert len(page2["items"]) == 2
    assert page2["next_cursor"] is None


def test_cursor_last_page_no_cursor(client: TestClient):
    for i in range(3):
        client.post("/books/", json={**FIXTURE, "title": f"Book{i}"})
    data = client.get("/books/?limit=10").json()
    assert data["next_cursor"] is None


def test_cursor_invalid_token_422(client: TestClient):
    assert client.get("/books/?cursor=not-valid-base64!!").status_code == 422


def test_cursor_sort_by_title(client: TestClient):
    for t in ["Zemlia", "Eneyida", "Kobzar"]:
        client.post("/books/", json={**FIXTURE, "title": t})
    items = client.get("/books/?sort_by=title").json()["items"]
    titles = [b["title"] for b in items]
    assert titles == sorted(titles, key=str.lower)


def test_cursor_sort_by_year(client: TestClient):
    for y in [1911, 1798, 1840]:
        client.post("/books/", json={**FIXTURE, "title": f"B{y}", "year": y})
    items = client.get("/books/?sort_by=year").json()["items"]
    years = [b["year"] for b in items]
    assert years == sorted(years)


def test_filter_status_free(client: TestClient):
    client.post("/books/", json={**FIXTURE, "status": "free"})
    client.post("/books/", json={**FIXTURE, "title": "B", "status": "on_loan"})
    data = client.get("/books/?status=free").json()
    assert len(data["items"]) == 1 and data["items"][0]["status"] == "free"


def test_filter_author_partial(client: TestClient):
    client.post("/books/", json={**FIXTURE, "author": "Ivan Franko"})
    client.post("/books/", json={**FIXTURE, "title": "X", "author": "Lesya Ukrainka"})
    assert len(client.get("/books/?author=franko").json()["items"]) == 1


def test_limit_max_422(client: TestClient):
    assert client.get("/books/?limit=0").status_code == 422


# ── GET single ────────────────────────────────────────────────────────────────

def test_get_200(client: TestClient):
    uid = client.post("/books/", json=FIXTURE).json()["id"]
    assert client.get(f"/books/{uid}").status_code == 200


def test_get_data(client: TestClient):
    uid = client.post("/books/", json=FIXTURE).json()["id"]
    assert client.get(f"/books/{uid}").json()["pages"] == FIXTURE["pages"]


def test_get_404(client: TestClient):
    assert client.get("/books/00000000-0000-0000-0000-000000000000").status_code == 404


# ── DELETE ────────────────────────────────────────────────────────────────────

def test_delete_204(client: TestClient):
    uid = client.post("/books/", json=FIXTURE).json()["id"]
    assert client.delete(f"/books/{uid}").status_code == 204


def test_delete_removes(client: TestClient):
    uid = client.post("/books/", json=FIXTURE).json()["id"]
    client.delete(f"/books/{uid}")
    assert client.get(f"/books/{uid}").status_code == 404


def test_delete_idempotent(client: TestClient):
    uid = client.post("/books/", json=FIXTURE).json()["id"]
    client.delete(f"/books/{uid}")
    assert client.delete(f"/books/{uid}").status_code == 204


def test_delete_unknown_204(client: TestClient):
    assert client.delete("/books/00000000-0000-0000-0000-000000000000").status_code == 204
