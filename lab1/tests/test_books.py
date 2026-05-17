import pytest
from fastapi.testclient import TestClient

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from models.book import library_store

client = TestClient(app)

FIXTURE = {
    "title": "Kobzar",
    "author": "Taras Shevchenko",
    "year": 1840,
    "pages": 312,
    "summary": "Zbirka poetychnykh tvoriv",
    "status": "free",
}


@pytest.fixture(autouse=True)
def reset_store():
    library_store.clear()
    yield
    library_store.clear()


# ── POST ──────────────────────────────────────────────────────────────────────

def test_post_returns_201():
    assert client.post("/books/", json=FIXTURE).status_code == 201


def test_post_response_has_id():
    data = client.post("/books/", json=FIXTURE).json()
    assert "id" in data and len(data["id"]) == 36


def test_post_two_books_get_different_ids():
    a = client.post("/books/", json=FIXTURE).json()
    b = client.post("/books/", json=FIXTURE).json()
    assert a["id"] != b["id"]


def test_post_fields_match_input():
    data = client.post("/books/", json=FIXTURE).json()
    assert data["title"] == FIXTURE["title"]
    assert data["author"] == FIXTURE["author"]
    assert data["year"] == FIXTURE["year"]
    assert data["pages"] == FIXTURE["pages"]
    assert data["summary"] == FIXTURE["summary"]
    assert data["status"] == "free"


def test_post_default_status_is_free():
    book = {k: v for k, v in FIXTURE.items() if k != "status"}
    assert client.post("/books/", json=book).json()["status"] == "free"


def test_post_on_loan_status():
    data = client.post("/books/", json={**FIXTURE, "status": "on_loan"}).json()
    assert data["status"] == "on_loan"


def test_post_without_pages_is_none():
    book = {k: v for k, v in FIXTURE.items() if k != "pages"}
    assert client.post("/books/", json=book).json()["pages"] is None


def test_post_without_summary_is_none():
    book = {k: v for k, v in FIXTURE.items() if k != "summary"}
    assert client.post("/books/", json=book).json()["summary"] is None


def test_post_missing_title_returns_422():
    assert client.post("/books/", json={k: v for k, v in FIXTURE.items() if k != "title"}).status_code == 422


def test_post_missing_author_returns_422():
    assert client.post("/books/", json={k: v for k, v in FIXTURE.items() if k != "author"}).status_code == 422


def test_post_missing_year_returns_422():
    assert client.post("/books/", json={k: v for k, v in FIXTURE.items() if k != "year"}).status_code == 422


def test_post_empty_title_returns_422():
    assert client.post("/books/", json={**FIXTURE, "title": ""}).status_code == 422


def test_post_year_out_of_range_low():
    assert client.post("/books/", json={**FIXTURE, "year": 999}).status_code == 422


def test_post_year_out_of_range_high():
    assert client.post("/books/", json={**FIXTURE, "year": 2101}).status_code == 422


def test_post_invalid_status_returns_422():
    assert client.post("/books/", json={**FIXTURE, "status": "missing"}).status_code == 422


def test_post_pages_zero_returns_422():
    assert client.post("/books/", json={**FIXTURE, "pages": 0}).status_code == 422


# ── GET list ──────────────────────────────────────────────────────────────────

def test_get_list_empty():
    assert client.get("/books/").json() == []


def test_get_list_returns_all():
    client.post("/books/", json=FIXTURE)
    client.post("/books/", json={**FIXTURE, "title": "Lisova Pisnya"})
    assert len(client.get("/books/").json()) == 2


def test_filter_status_free():
    client.post("/books/", json={**FIXTURE, "status": "free"})
    client.post("/books/", json={**FIXTURE, "title": "B", "status": "on_loan"})
    result = client.get("/books/?status=free").json()
    assert len(result) == 1 and result[0]["status"] == "free"


def test_filter_status_on_loan():
    client.post("/books/", json={**FIXTURE, "status": "on_loan"})
    client.post("/books/", json={**FIXTURE, "title": "B", "status": "free"})
    result = client.get("/books/?status=on_loan").json()
    assert len(result) == 1 and result[0]["status"] == "on_loan"


def test_filter_author_partial_case_insensitive():
    client.post("/books/", json={**FIXTURE, "author": "Ivan Franko"})
    client.post("/books/", json={**FIXTURE, "title": "X", "author": "Lesya Ukrainka"})
    result = client.get("/books/?author=franko").json()
    assert len(result) == 1


def test_filter_pages_min():
    client.post("/books/", json={**FIXTURE, "title": "Short", "pages": 50})
    client.post("/books/", json={**FIXTURE, "title": "Long", "pages": 500})
    result = client.get("/books/?pages_min=100").json()
    assert len(result) == 1 and result[0]["title"] == "Long"


def test_filter_no_match():
    client.post("/books/", json=FIXTURE)
    assert client.get("/books/?author=NobodyXXX").json() == []


def test_sort_by_title_alphabetical():
    for t in ["Zemlia", "Eneyida", "Kobzar"]:
        client.post("/books/", json={**FIXTURE, "title": t})
    titles = [b["title"] for b in client.get("/books/?sort_by=title").json()]
    assert titles == sorted(titles, key=str.lower)


def test_sort_by_year():
    for y in [1911, 1798, 1840]:
        client.post("/books/", json={**FIXTURE, "title": f"B{y}", "year": y})
    years = [b["year"] for b in client.get("/books/?sort_by=year").json()]
    assert years == sorted(years)


def test_sort_invalid_field_422():
    assert client.get("/books/?sort_by=rating").status_code == 422


# ── GET single ───────────────────────────────────────────────────────────────

def test_get_by_id_200():
    uid = client.post("/books/", json=FIXTURE).json()["id"]
    assert client.get(f"/books/{uid}").status_code == 200


def test_get_by_id_data_correct():
    uid = client.post("/books/", json=FIXTURE).json()["id"]
    data = client.get(f"/books/{uid}").json()
    assert data["title"] == FIXTURE["title"]
    assert data["pages"] == FIXTURE["pages"]


def test_get_nonexistent_404():
    assert client.get("/books/00000000-0000-0000-0000-000000000000").status_code == 404


def test_get_404_has_detail():
    assert "detail" in client.get("/books/00000000-0000-0000-0000-000000000000").json()


# ── DELETE ────────────────────────────────────────────────────────────────────

def test_delete_returns_204():
    uid = client.post("/books/", json=FIXTURE).json()["id"]
    assert client.delete(f"/books/{uid}").status_code == 204


def test_delete_removes_entry():
    uid = client.post("/books/", json=FIXTURE).json()["id"]
    client.delete(f"/books/{uid}")
    assert client.get(f"/books/{uid}").status_code == 404


def test_delete_idempotent():
    uid = client.post("/books/", json=FIXTURE).json()["id"]
    client.delete(f"/books/{uid}")
    assert client.delete(f"/books/{uid}").status_code == 204


def test_delete_unknown_uid_204():
    assert client.delete("/books/00000000-0000-0000-0000-000000000000").status_code == 204


def test_delete_leaves_other_entries_intact():
    uid1 = client.post("/books/", json=FIXTURE).json()["id"]
    uid2 = client.post("/books/", json={**FIXTURE, "title": "Eneyida"}).json()["id"]
    client.delete(f"/books/{uid1}")
    assert client.get(f"/books/{uid2}").status_code == 200
