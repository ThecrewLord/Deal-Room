from marshmallow import Schema, fields, validate


class AccountCreateSchema(Schema):

    account_name = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=200),
    )

    industry = fields.Str(
        allow_none=True,
        validate=validate.Length(max=100),
    )

    website = fields.Str(
        allow_none=True,
        validate=validate.Length(max=255),
    )

    phone = fields.Str(
        allow_none=True,
        validate=validate.Length(max=50),
    )

    country = fields.Str(
        allow_none=True,
        validate=validate.Length(max=100),
    )

    state = fields.Str(
        allow_none=True,
        validate=validate.Length(max=100),
    )

    city = fields.Str(
        allow_none=True,
        validate=validate.Length(max=100),
    )

    address = fields.Str(
        allow_none=True,
    )


class AccountUpdateSchema(Schema):

    account_name = fields.Str(
        validate=validate.Length(min=2, max=200),
    )

    industry = fields.Str(
        allow_none=True,
        validate=validate.Length(max=100),
    )

    website = fields.Str(
        allow_none=True,
        validate=validate.Length(max=255),
    )

    phone = fields.Str(
        allow_none=True,
        validate=validate.Length(max=50),
    )

    country = fields.Str(
        allow_none=True,
        validate=validate.Length(max=100),
    )

    state = fields.Str(
        allow_none=True,
        validate=validate.Length(max=100),
    )

    city = fields.Str(
        allow_none=True,
        validate=validate.Length(max=100),
    )

    address = fields.Str(
        allow_none=True,
    )