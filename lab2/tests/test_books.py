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

def test_post_returns_201(client: TestClient):
    assert client.post("/books/", json=FIXTURE).status_code == 201


def test_post_fields_match(client: TestClient):
    data = client.post("/books/", json=FIXTURE).json()
    assert data["title"] == FIXTURE["title"]
    assert data["author"] == FIXTURE["author"]
    assert data["year"] == FIXTURE["year"]
    assert data["pages"] == FIXTURE["pages"]
    assert data["status"] == "free"


def test_post_unique_ids(client: TestClient):
    a = client.post("/books/", json=FIXTURE).json()
    b = client.post("/books/", json=FIXTURE).json()
    assert a["id"] != b["id"] and len(a["id"]) == 36


def test_post_default_status_free(client: TestClient):
    book = {k: v for k, v in FIXTURE.items() if k != "status"}
    assert client.post("/books/", json=book).json()["status"] == "free"


def test_post_on_loan(client: TestClient):
    assert client.post("/books/", json={**FIXTURE, "status": "on_loan"}).json()["status"] == "on_loan"


def test_post_no_summary_is_none(client: TestClient):
    book = {k: v for k, v in FIXTURE.items() if k != "summary"}
    assert client.post("/books/", json=book).json()["summary"] is None


def test_post_no_pages_is_none(client: TestClient):
    book = {k: v for k, v in FIXTURE.items() if k != "pages"}
    assert client.post("/books/", json=book).json()["pages"] is None


def test_post_missing_title_422(client: TestClient):
    assert client.post("/books/", json={k: v for k, v in FIXTURE.items() if k != "title"}).status_code == 422


def test_post_missing_author_422(client: TestClient):
    assert client.post("/books/", json={k: v for k, v in FIXTURE.items() if k != "author"}).status_code == 422


def test_post_missing_year_422(client: TestClient):
    assert client.post("/books/", json={k: v for k, v in FIXTURE.items() if k != "year"}).status_code == 422


def test_post_empty_title_422(client: TestClient):
    assert client.post("/books/", json={**FIXTURE, "title": ""}).status_code == 422


def test_post_year_too_low_422(client: TestClient):
    assert client.post("/books/", json={**FIXTURE, "year": 999}).status_code == 422


def test_post_year_too_high_422(client: TestClient):
    assert client.post("/books/", json={**FIXTURE, "year": 2101}).status_code == 422


def test_post_invalid_status_422(client: TestClient):
    assert client.post("/books/", json={**FIXTURE, "status": "broken"}).status_code == 422


# ── GET list ──────────────────────────────────────────────────────────────────

def test_list_empty(client: TestClient):
    data = client.get("/books/").json()
    assert data["items"] == [] and data["total"] == 0


def test_list_structure(client: TestClient):
    client.post("/books/", json=FIXTURE)
    data = client.get("/books/").json()
    assert all(k in data for k in ("items", "total", "limit", "offset"))


def test_list_total_count(client: TestClient):
    client.post("/books/", json=FIXTURE)
    client.post("/books/", json={**FIXTURE, "title": "Eneyida"})
    assert client.get("/books/").json()["total"] == 2


def test_filter_status_free(client: TestClient):
    client.post("/books/", json={**FIXTURE, "status": "free"})
    client.post("/books/", json={**FIXTURE, "title": "B", "status": "on_loan"})
    data = client.get("/books/?status=free").json()
    assert data["total"] == 1 and data["items"][0]["status"] == "free"


def test_filter_status_on_loan(client: TestClient):
    client.post("/books/", json={**FIXTURE, "status": "on_loan"})
    client.post("/books/", json={**FIXTURE, "title": "B", "status": "free"})
    data = client.get("/books/?status=on_loan").json()
    assert data["total"] == 1 and data["items"][0]["status"] == "on_loan"


def test_filter_author_partial(client: TestClient):
    client.post("/books/", json={**FIXTURE, "author": "Ivan Franko"})
    client.post("/books/", json={**FIXTURE, "title": "X", "author": "Lesya Ukrainka"})
    assert client.get("/books/?author=franko").json()["total"] == 1


def test_filter_author_case_insensitive(client: TestClient):
    client.post("/books/", json={**FIXTURE, "author": "Shevchenko"})
    assert client.get("/books/?author=SHEVCHENKO").json()["total"] == 1


def test_filter_no_match(client: TestClient):
    client.post("/books/", json=FIXTURE)
    data = client.get("/books/?author=NobodyXXX").json()
    assert data["items"] == [] and data["total"] == 0


def test_sort_by_title(client: TestClient):
    for t in ["Zemlia", "Eneyida", "Kobzar"]:
        client.post("/books/", json={**FIXTURE, "title": t})
    titles = [b["title"] for b in client.get("/books/?sort_by=title").json()["items"]]
    assert titles == sorted(titles, key=str.lower)


def test_sort_by_year(client: TestClient):
    for y in [1911, 1798, 1840]:
        client.post("/books/", json={**FIXTURE, "title": f"B{y}", "year": y})
    years = [b["year"] for b in client.get("/books/?sort_by=year").json()["items"]]
    assert years == sorted(years)


def test_sort_invalid_422(client: TestClient):
    assert client.get("/books/?sort_by=pages").status_code == 422


# ── Pagination ────────────────────────────────────────────────────────────────

def test_pagination_default(client: TestClient):
    for i in range(12):
        client.post("/books/", json={**FIXTURE, "title": f"Book{i}"})
    data = client.get("/books/").json()
    assert data["limit"] == 10 and data["total"] == 12 and len(data["items"]) == 10


def test_pagination_custom_limit(client: TestClient):
    for i in range(5):
        client.post("/books/", json={**FIXTURE, "title": f"Book{i}"})
    data = client.get("/books/?limit=3").json()
    assert len(data["items"]) == 3 and data["total"] == 5


def test_pagination_offset(client: TestClient):
    for i in range(5):
        client.post("/books/", json={**FIXTURE, "title": f"Book{i}"})
    data = client.get("/books/?offset=3").json()
    assert len(data["items"]) == 2 and data["offset"] == 3


def test_pagination_limit_offset(client: TestClient):
    for i in range(10):
        client.post("/books/", json={**FIXTURE, "title": f"Book{i:02d}"})
    data = client.get("/books/?sort_by=title&limit=3&offset=3").json()
    assert len(data["items"]) == 3 and data["items"][0]["title"] == "Book03"


def test_pagination_offset_over_total(client: TestClient):
    client.post("/books/", json=FIXTURE)
    data = client.get("/books/?offset=100").json()
    assert data["items"] == [] and data["total"] == 1


def test_pagination_limit_zero_422(client: TestClient):
    assert client.get("/books/?limit=0").status_code == 422


def test_pagination_offset_negative_422(client: TestClient):
    assert client.get("/books/?offset=-1").status_code == 422


def test_pagination_limit_over_max_422(client: TestClient):
    assert client.get("/books/?limit=101").status_code == 422


# ── GET single ────────────────────────────────────────────────────────────────

def test_get_by_id_200(client: TestClient):
    uid = client.post("/books/", json=FIXTURE).json()["id"]
    assert client.get(f"/books/{uid}").status_code == 200


def test_get_by_id_data(client: TestClient):
    uid = client.post("/books/", json=FIXTURE).json()["id"]
    data = client.get(f"/books/{uid}").json()
    assert data["title"] == FIXTURE["title"] and data["pages"] == FIXTURE["pages"]


def test_get_nonexistent_404(client: TestClient):
    assert client.get("/books/00000000-0000-0000-0000-000000000000").status_code == 404


def test_get_404_detail(client: TestClient):
    assert "detail" in client.get("/books/00000000-0000-0000-0000-000000000000").json()


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


def test_delete_leaves_others(client: TestClient):
    uid1 = client.post("/books/", json=FIXTURE).json()["id"]
    uid2 = client.post("/books/", json={**FIXTURE, "title": "Eneyida"}).json()["id"]
    client.delete(f"/books/{uid1}")
    assert client.get(f"/books/{uid2}").status_code == 200
