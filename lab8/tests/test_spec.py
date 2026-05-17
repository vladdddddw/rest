"""
OpenAPI spec structural validation — no external service required.
"""
import pytest


def test_spec_loads(spec):
    assert spec is not None


def test_openapi_version(spec):
    assert spec["openapi"].startswith("3.")


def test_info_title(spec):
    assert spec["info"]["title"] == "Book Catalog API"
    assert "version" in spec["info"]


def test_has_servers(spec):
    assert len(spec.get("servers", [])) >= 1


def test_has_auth_and_books_tags(spec):
    names = {t["name"] for t in spec.get("tags", [])}
    assert "auth" in names and "books" in names


def test_bearer_security_scheme(spec):
    schemes = spec["components"]["securitySchemes"]
    assert "BearerAuth" in schemes
    assert schemes["BearerAuth"]["scheme"] == "bearer"


def test_global_security_is_bearer(spec):
    assert any("BearerAuth" in s for s in spec.get("security", []))


def test_auth_endpoints_are_public(spec):
    for path in ["/auth/login", "/auth/register", "/auth/refresh", "/auth/logout"]:
        for method in spec["paths"].get(path, {}).values():
            if isinstance(method, dict):
                assert method.get("security") == [], f"{path} should be public"


def test_register_responses(spec):
    r = spec["paths"]["/auth/register"]["post"]["responses"]
    assert "201" in r and "409" in r and "422" in r


def test_login_responses(spec):
    r = spec["paths"]["/auth/login"]["post"]["responses"]
    assert "200" in r and "401" in r and "429" in r


def test_refresh_responses(spec):
    r = spec["paths"]["/auth/refresh"]["post"]["responses"]
    assert "200" in r and "401" in r


def test_logout_responses(spec):
    assert "200" in spec["paths"]["/auth/logout"]["post"]["responses"]


def test_books_list_exists(spec):
    assert "/books/" in spec["paths"]
    assert "get" in spec["paths"]["/books/"] and "post" in spec["paths"]["/books/"]


def test_get_books_responses(spec):
    r = spec["paths"]["/books/"]["get"]["responses"]
    assert "200" in r and "429" in r


def test_post_books_responses(spec):
    r = spec["paths"]["/books/"]["post"]["responses"]
    assert "201" in r and "401" in r and "422" in r


def test_book_detail_exists(spec):
    assert "/books/{book_id}" in spec["paths"]
    p = spec["paths"]["/books/{book_id}"]
    assert "get" in p and "delete" in p


def test_get_book_responses(spec):
    r = spec["paths"]["/books/{book_id}"]["get"]["responses"]
    assert "200" in r and "404" in r


def test_delete_book_responses(spec):
    r = spec["paths"]["/books/{book_id}"]["delete"]["responses"]
    assert "204" in r and "401" in r


def test_pagination_params(spec):
    params = {p["name"]: p for p in spec["paths"]["/books/"]["get"]["parameters"]}
    assert "limit" in params and "offset" in params
    assert params["limit"]["schema"]["default"] == 10


def test_filter_params_exist(spec):
    params = {p["name"]: p for p in spec["paths"]["/books/"]["get"]["parameters"]}
    assert "status" in params and "author" in params and "pages_min" in params


def test_status_enum_is_free_on_loan(spec):
    params = {p["name"]: p for p in spec["paths"]["/books/"]["get"]["parameters"]}
    enum = params["status"]["schema"]["enum"]
    assert "free" in enum and "on_loan" in enum


def test_sort_by_enum(spec):
    params = {p["name"]: p for p in spec["paths"]["/books/"]["get"]["parameters"]}
    assert set(params["sort_by"]["schema"]["enum"]) == {"title", "year"}


def test_required_schemas_present(spec):
    schemas = spec["components"]["schemas"]
    for name in ["Book", "BookIn", "BookListOut",
                 "UserRegister", "UserOut",
                 "LoginRequest", "TokenResponse", "RefreshRequest",
                 "Error", "ValidationError"]:
        assert name in schemas, f"Missing schema: {name}"


def test_book_schema_required_fields(spec):
    required = spec["components"]["schemas"]["Book"]["required"]
    for f in ("id", "title", "author", "year", "status"):
        assert f in required


def test_book_has_pages_and_summary(spec):
    props = spec["components"]["schemas"]["Book"]["properties"]
    assert "pages" in props and "summary" in props


def test_book_status_enum_values(spec):
    enum = spec["components"]["schemas"]["Book"]["properties"]["status"]["enum"]
    assert set(enum) == {"free", "on_loan"}


def test_book_in_requires_title_author_year(spec):
    required = spec["components"]["schemas"]["BookIn"]["required"]
    assert "title" in required and "author" in required and "year" in required


def test_year_constraints(spec):
    year = spec["components"]["schemas"]["BookIn"]["properties"]["year"]
    assert year["minimum"] == 1000 and year["maximum"] == 2100


def test_token_response_fields(spec):
    props = spec["components"]["schemas"]["TokenResponse"]["properties"]
    assert "access_token" in props and "refresh_token" in props and "token_type" in props


def test_book_list_out_fields(spec):
    props = spec["components"]["schemas"]["BookListOut"]["properties"]
    assert all(k in props for k in ("items", "total", "limit", "offset"))


def test_user_out_has_no_role(spec):
    props = spec["components"]["schemas"]["UserOut"]["properties"]
    assert "role" not in props
    assert "username" in props and "is_active" in props


def test_reusable_responses(spec):
    responses = spec["components"]["responses"]
    for name in ["Unauthorized", "NotFound", "UnprocessableEntity", "TooManyRequests"]:
        assert name in responses


def test_retry_after_header_in_429(spec):
    assert "Retry-After" in spec["components"]["responses"]["TooManyRequests"].get("headers", {})


def test_all_operations_have_operation_ids(spec):
    for path, item in spec["paths"].items():
        for method, op in item.items():
            if isinstance(op, dict) and method in ("get", "post", "put", "delete", "patch"):
                assert "operationId" in op, f"Missing operationId: {method.upper()} {path}"
