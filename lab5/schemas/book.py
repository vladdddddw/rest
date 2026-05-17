from marshmallow import Schema, fields, validate, EXCLUDE


class BookInSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    title = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    author = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    year = fields.Int(required=True, validate=validate.Range(min=1000, max=2100))
    pages = fields.Int(load_default=None, allow_none=True,
                       validate=validate.Range(min=1, max=10000))
    summary = fields.Str(load_default=None, allow_none=True,
                         validate=validate.Length(max=1000))
    status = fields.Str(load_default="free",
                        validate=validate.OneOf(["free", "on_loan"]))


class BookOutSchema(Schema):
    id = fields.Str()
    title = fields.Str()
    author = fields.Str()
    year = fields.Int()
    pages = fields.Int(allow_none=True)
    summary = fields.Str(allow_none=True)
    status = fields.Str()
