from flask import Flask
from flask_restful import Api
from flasgger import Swagger

from api.books import BookListResource, BookResource

app = Flask(__name__)
api = Api(app)

SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "swagger_ui": True,
    "specs_route": "/docs",
    "swagger_ui_bundle_js": "https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js",
    "swagger_ui_standalone_preset_js": "https://unpkg.com/swagger-ui-dist@5/swagger-ui-standalone-preset.js",
    "swagger_ui_css": "https://unpkg.com/swagger-ui-dist@5/swagger-ui.css",
    "jquery_js": "https://unpkg.com/jquery@3/dist/jquery.min.js",
}

SWAGGER_TEMPLATE = {
    "info": {
        "title": "Book Catalog API",
        "description": "REST API for managing a book catalog. Built with Flask + Flask-RESTful.",
        "version": "1.0.0",
    },
    "host": "localhost:8000",
    "basePath": "/",
    "schemes": ["http"],
    "definitions": {
        "Book": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "example": "550e8400-e29b-41d4-a716-446655440000"},
                "title": {"type": "string", "example": "Kobzar"},
                "author": {"type": "string", "example": "Taras Shevchenko"},
                "year": {"type": "integer", "example": 1840},
                "pages": {"type": "integer", "example": 312, "x-nullable": True},
                "summary": {"type": "string", "example": "Poetry collection", "x-nullable": True},
                "status": {"type": "string", "enum": ["free", "on_loan"], "example": "free"},
            },
        },
        "BookIn": {
            "type": "object",
            "required": ["title", "author", "year"],
            "properties": {
                "title": {"type": "string", "minLength": 1, "maxLength": 255, "example": "Kobzar"},
                "author": {"type": "string", "minLength": 1, "maxLength": 255, "example": "Taras Shevchenko"},
                "year": {"type": "integer", "minimum": 1000, "maximum": 2100, "example": 1840},
                "pages": {"type": "integer", "minimum": 1, "maximum": 10000, "example": 312, "x-nullable": True},
                "summary": {"type": "string", "example": "Poetry collection", "x-nullable": True},
                "status": {"type": "string", "enum": ["free", "on_loan"], "default": "free"},
            },
        },
        "BookListResponse": {
            "type": "object",
            "properties": {
                "items": {"type": "array", "items": {"$ref": "#/definitions/Book"}},
                "total": {"type": "integer", "example": 42},
                "limit": {"type": "integer", "example": 10},
                "offset": {"type": "integer", "example": 0},
            },
        },
        "ValidationError": {
            "type": "object",
            "properties": {
                "errors": {
                    "type": "object",
                    "additionalProperties": {"type": "array", "items": {"type": "string"}},
                    "example": {"title": ["Missing data for required field."]},
                }
            },
        },
        "NotFound": {
            "type": "object",
            "properties": {"detail": {"type": "string", "example": "Not found"}},
        },
    },
}

swagger = Swagger(app, config=SWAGGER_CONFIG, template=SWAGGER_TEMPLATE)

api.add_resource(BookListResource, "/books/")
api.add_resource(BookResource, "/books/<string:book_id>")


@app.get("/")
def index():
    return {"message": "Book Catalog API"}


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
