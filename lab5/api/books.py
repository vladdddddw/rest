from flask import request, make_response
from flask_restful import Resource
from marshmallow import ValidationError

from schemas.book import BookInSchema, BookOutSchema
from services import book_service

_in_schema = BookInSchema()
_out_schema = BookOutSchema()


class BookListResource(Resource):
    def get(self):
        """
        List books with filtering and pagination.
        ---
        tags:
          - books
        parameters:
          - name: status
            in: query
            type: string
            enum: [free, on_loan]
            description: Filter by availability
          - name: author
            in: query
            type: string
            description: Author name (partial, case-insensitive)
          - name: pages_min
            in: query
            type: integer
            minimum: 1
            description: Minimum number of pages
          - name: sort_by
            in: query
            type: string
            enum: [title, year]
            description: Sort field
          - name: limit
            in: query
            type: integer
            default: 10
            minimum: 1
            maximum: 100
          - name: offset
            in: query
            type: integer
            default: 0
            minimum: 0
        responses:
          200:
            description: Paginated book list
            schema:
              $ref: '#/definitions/BookListResponse'
          422:
            description: Invalid parameters
            schema:
              $ref: '#/definitions/ValidationError'
        """
        status = request.args.get("status")
        author = request.args.get("author")
        sort_by = request.args.get("sort_by")

        if status is not None and status not in ("free", "on_loan"):
            return {"errors": {"status": ["Must be one of: free, on_loan"]}}, 422
        if sort_by is not None and sort_by not in ("title", "year"):
            return {"errors": {"sort_by": ["Must be one of: title, year"]}}, 422

        try:
            limit = int(request.args.get("limit", 10))
            offset = int(request.args.get("offset", 0))
            pages_min_raw = request.args.get("pages_min")
            pages_min = int(pages_min_raw) if pages_min_raw else None
        except (ValueError, TypeError):
            return {"errors": {"params": ["Invalid integer value"]}}, 422

        if not (1 <= limit <= 100):
            return {"errors": {"limit": ["Must be between 1 and 100"]}}, 422
        if offset < 0:
            return {"errors": {"offset": ["Cannot be negative"]}}, 422

        records, total = book_service.list_books(
            status=status, author=author, pages_min=pages_min,
            sort_by=sort_by, limit=limit, offset=offset,
        )
        return {
            "items": [_out_schema.dump(r) for r in records],
            "total": total,
            "limit": limit,
            "offset": offset,
        }, 200

    def post(self):
        """
        Add a new book to the library.
        ---
        tags:
          - books
        consumes:
          - application/json
        parameters:
          - in: body
            name: body
            required: true
            schema:
              $ref: '#/definitions/BookIn'
        responses:
          201:
            description: Created
            schema:
              $ref: '#/definitions/Book'
          422:
            description: Validation error
            schema:
              $ref: '#/definitions/ValidationError'
        """
        payload = request.get_json(silent=True) or {}
        try:
            data = _in_schema.load(payload)
        except ValidationError as exc:
            return {"errors": exc.messages}, 422

        entry = book_service.register_book(data)
        return _out_schema.dump(entry), 201


class BookResource(Resource):
    def get(self, book_id):
        """
        Retrieve a single book by ID.
        ---
        tags:
          - books
        parameters:
          - name: book_id
            in: path
            type: string
            required: true
        responses:
          200:
            description: Book found
            schema:
              $ref: '#/definitions/Book'
          404:
            description: Not found
            schema:
              $ref: '#/definitions/NotFound'
        """
        entry = book_service.get_entry(book_id)
        if entry is None:
            return {"detail": "Not found"}, 404
        return _out_schema.dump(entry), 200

    def delete(self, book_id):
        """
        Remove a book by ID (idempotent).
        ---
        tags:
          - books
        parameters:
          - name: book_id
            in: path
            type: string
            required: true
        responses:
          204:
            description: Deleted (or never existed)
        """
        book_service.drop_book(book_id)
        return make_response("", 204)
