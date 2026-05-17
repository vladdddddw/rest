from flask.testing import FlaskClient

FIXTURE = {
    "title": "Kobzar",
    "author": "Taras Shevchenko",
    "year": 1840,
    "pages": 312,
    "summary": "Klasychna zbirka",
    "status": "free",
}


# ── POST ──────────────────────────────────────────────────────────────────────

def test_post_201(client: FlaskClient):
    assert client.post("/books/", json=FIXTURE).status_code == 201


def test_post_fields(client: FlaskClient):
    data = client.post("/books/", json=FIXTURE).get_json()
    assert data["title"] == FIXTURE["title"]
    assert data["pages"] == FIXTURE["pages"]
    assert data["status"] == "free"


def test_post_unique_ids(client: FlaskClient):
    a = client.post("/books/", json=FIXTURE).get_json()
    b = client.post("/books/", json=FIXTURE).get_json()
    assert len(a["id"]) == 36 and a["id"] != b["id"]


def test_post_default_free(client: FlaskClient):
    book = {k: v for k, v in FIXTURE.items() if k != "status"}
    assert client.post("/books/", json=book).get_json()["status"] == "free"


def test_post_on_loan(client: FlaskClient):
    assert client.post("/books/", json={**FIXTURE, "status": "on_loan"}).get_json()["status"] == "on_loan"


def test_post_no_pages_none(client: FlaskClient):
    book = {k: v for k, v in FIXTURE.items() if k != "pages"}
    assert client.post("/books/", json=book).get_json()["pages"] is None


def test_post_missing_title_422(client: FlaskClient):
    assert client.post("/books/", json={k: v for k, v in FIXTURE.items() if k != "title"}).status_code == 422


def test_post_missing_author_422(client: FlaskClient):
    assert client.post("/books/", json={k: v for k, v in FIXTURE.items() if k != "author"}).status_code == 422


def test_post_missing_year_422(client: FlaskClient):
    assert client.post("/books/", json={k: v for k, v in FIXTURE.items() if k != "year"}).status_code == 422


def test_post_empty_title_422(client: FlaskClient):
    assert client.post("/books/", json={**FIXTURE, "title": ""}).status_code == 422


def test_post_year_low_422(client: FlaskClient):
    assert client.post("/books/", json={**FIXTURE, "year": 999}).status_code == 422


def test_post_year_high_422(client: FlaskClient):
    assert client.post("/books/", json={**FIXTURE, "year": 2101}).status_code == 422


def test_post_invalid_status_422(client: FlaskClient):
    assert client.post("/books/", json={**FIXTURE, "status": "broken"}).status_code == 422


def test_post_422_has_errors(client: FlaskClient):
    book = {k: v for k, v in FIXTURE.items() if k != "title"}
    assert "errors" in client.post("/books/", json=book).get_json()


# ── GET list ──────────────────────────────────────────────────────────────────

def test_list_200(client: FlaskClient):
    assert client.get("/books/").status_code == 200


def test_list_empty(client: FlaskClient):
    data = client.get("/books/").get_json()
    assert data["items"] == [] and data["total"] == 0


def test_list_structure(client: FlaskClient):
    client.post("/books/", json=FIXTURE)
    data = client.get("/books/").get_json()
    assert all(k in data for k in ("items", "total", "limit", "offset"))


def test_list_count(client: FlaskClient):
    client.post("/books/", json=FIXTURE)
    client.post("/books/", json={**FIXTURE, "title": "Eneyida"})
    assert client.get("/books/").get_json()["total"] == 2


def test_filter_status_free(client: FlaskClient):
    client.post("/books/", json={**FIXTURE, "status": "free"})
    client.post("/books/", json={**FIXTURE, "title": "B", "status": "on_loan"})
    data = client.get("/books/?status=free").get_json()
    assert data["total"] == 1 and data["items"][0]["status"] == "free"


def test_filter_status_on_loan(client: FlaskClient):
    client.post("/books/", json={**FIXTURE, "status": "on_loan"})
    client.post("/books/", json={**FIXTURE, "title": "B", "status": "free"})
    data = client.get("/books/?status=on_loan").get_json()
    assert data["total"] == 1


def test_filter_status_invalid_422(client: FlaskClient):
    assert client.get("/books/?status=unknown").status_code == 422


def test_filter_author_partial(client: FlaskClient):
    client.post("/books/", json={**FIXTURE, "author": "Ivan Franko"})
    client.post("/books/", json={**FIXTURE, "title": "X", "author": "Lesya Ukrainka"})
    assert client.get("/books/?author=franko").get_json()["total"] == 1


def test_filter_author_case_insensitive(client: FlaskClient):
    client.post("/books/", json={**FIXTURE, "author": "Shevchenko"})
    assert client.get("/books/?author=SHEVCHENKO").get_json()["total"] == 1


def test_filter_pages_min(client: FlaskClient):
    client.post("/books/", json={**FIXTURE, "title": "Short", "pages": 50})
    client.post("/books/", json={**FIXTURE, "title": "Long", "pages": 500})
    data = client.get("/books/?pages_min=100").get_json()
    assert data["total"] == 1 and data["items"][0]["title"] == "Long"


def test_sort_by_title(client: FlaskClient):
    for t in ["Zemlia", "Eneyida", "Kobzar"]:
        client.post("/books/", json={**FIXTURE, "title": t})
    items = client.get("/books/?sort_by=title").get_json()["items"]
    titles = [b["title"] for b in items]
    assert titles == sorted(titles, key=str.lower)


def test_sort_by_year(client: FlaskClient):
    for y in [1911, 1798, 1840]:
        client.post("/books/", json={**FIXTURE, "title": f"B{y}", "year": y})
    years = [b["year"] for b in client.get("/books/?sort_by=year").get_json()["items"]]
    assert years == sorted(years)


def test_sort_invalid_422(client: FlaskClient):
    assert client.get("/books/?sort_by=rating").status_code == 422


def test_pagination_default(client: FlaskClient):
    for i in range(12):
        client.post("/books/", json={**FIXTURE, "title": f"Book{i:02d}"})
    data = client.get("/books/").get_json()
    assert data["limit"] == 10 and data["total"] == 12 and len(data["items"]) == 10


def test_pagination_limit(client: FlaskClient):
    for i in range(5):
        client.post("/books/", json={**FIXTURE, "title": f"Book{i}"})
    data = client.get("/books/?limit=3").get_json()
    assert len(data["items"]) == 3 and data["total"] == 5


def test_pagination_offset(client: FlaskClient):
    for i in range(5):
        client.post("/books/", json={**FIXTURE, "title": f"Book{i:02d}"})
    data = client.get("/books/?sort_by=title&offset=3").get_json()
    assert len(data["items"]) == 2 and data["total"] == 5


def test_pagination_limit_offset(client: FlaskClient):
    for i in range(10):
        client.post("/books/", json={**FIXTURE, "title": f"Book{i:02d}"})
    data = client.get("/books/?sort_by=title&limit=3&offset=3").get_json()
    assert len(data["items"]) == 3 and data["items"][0]["title"] == "Book03"


def test_pagination_limit_zero_422(client: FlaskClient):
    assert client.get("/books/?limit=0").status_code == 422


def test_pagination_offset_negative_422(client: FlaskClient):
    assert client.get("/books/?offset=-1").status_code == 422


def test_pagination_limit_over_max_422(client: FlaskClient):
    assert client.get("/books/?limit=101").status_code == 422


# ── GET single ────────────────────────────────────────────────────────────────

def test_get_200(client: FlaskClient):
    uid = client.post("/books/", json=FIXTURE).get_json()["id"]
    assert client.get(f"/books/{uid}").status_code == 200


def test_get_data(client: FlaskClient):
    uid = client.post("/books/", json=FIXTURE).get_json()["id"]
    data = client.get(f"/books/{uid}").get_json()
    assert data["pages"] == FIXTURE["pages"]


def test_get_404(client: FlaskClient):
    assert client.get("/books/00000000-0000-0000-0000-000000000000").status_code == 404


def test_get_404_detail(client: FlaskClient):
    assert "detail" in client.get("/books/00000000-0000-0000-0000-000000000000").get_json()


# ── DELETE ────────────────────────────────────────────────────────────────────

def test_delete_204(client: FlaskClient):
    uid = client.post("/books/", json=FIXTURE).get_json()["id"]
    assert client.delete(f"/books/{uid}").status_code == 204


def test_delete_removes(client: FlaskClient):
    uid = client.post("/books/", json=FIXTURE).get_json()["id"]
    client.delete(f"/books/{uid}")
    assert client.get(f"/books/{uid}").status_code == 404


def test_delete_idempotent(client: FlaskClient):
    uid = client.post("/books/", json=FIXTURE).get_json()["id"]
    client.delete(f"/books/{uid}")
    assert client.delete(f"/books/{uid}").status_code == 204


def test_delete_unknown_204(client: FlaskClient):
    assert client.delete("/books/00000000-0000-0000-0000-000000000000").status_code == 204


def test_delete_leaves_others(client: FlaskClient):
    uid1 = client.post("/books/", json=FIXTURE).get_json()["id"]
    uid2 = client.post("/books/", json={**FIXTURE, "title": "Eneyida"}).get_json()["id"]
    client.delete(f"/books/{uid1}")
    assert client.get(f"/books/{uid2}").status_code == 200


# ── Swagger / OpenAPI ─────────────────────────────────────────────────────────

def test_swagger_ui_accessible(client: FlaskClient):
    assert client.get("/docs").status_code == 200


def test_openapi_spec_accessible(client: FlaskClient):
    assert client.get("/apispec.json").status_code == 200


def test_openapi_spec_info(client: FlaskClient):
    spec = client.get("/apispec.json").get_json()
    assert spec["info"]["title"] == "Book Catalog API"
    assert spec["info"]["version"] == "1.0.0"


def test_openapi_spec_paths(client: FlaskClient):
    spec = client.get("/apispec.json").get_json()
    assert "/books/" in spec["paths"] and "/books/{book_id}" in spec["paths"]


def test_openapi_spec_definitions(client: FlaskClient):
    spec = client.get("/apispec.json").get_json()
    defs = spec.get("definitions", {})
    assert "Book" in defs and "BookIn" in defs and "BookListResponse" in defs


def test_openapi_book_has_fields(client: FlaskClient):
    spec = client.get("/apispec.json").get_json()
    props = spec["definitions"]["Book"]["properties"]
    for f in ("id", "title", "author", "year", "pages", "status"):
        assert f in props


def test_openapi_status_enum_values(client: FlaskClient):
    spec = client.get("/apispec.json").get_json()
    status_enum = spec["definitions"]["Book"]["properties"]["status"]["enum"]
    assert "free" in status_enum and "on_loan" in status_enum
