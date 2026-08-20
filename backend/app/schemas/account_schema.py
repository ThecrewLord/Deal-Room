from marshmallow import Schema, fields, validate


class AccountCreateSchema(Schema):

    account_name = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=200),
    )

    industry = fields.Str()

    website = fields.Str()

    phone = fields.Str()

    country = fields.Str()

    state = fields.Str()

    city = fields.Str()

    address = fields.Str()


class AccountUpdateSchema(Schema):

    account_name = fields.Str(
        validate=validate.Length(min=2, max=200),
    )

    industry = fields.Str()

    website = fields.Str()

    phone = fields.Str()

    country = fields.Str()

    state = fields.Str()

    city = fields.Str()

    address = fields.Str()

    is_active = fields.Bool()

    updated_at = fields.DateTime(required=True)


class AccountResponseSchema(Schema):

    account_id = fields.Int()

    account_name = fields.Str()

    industry = fields.Str()

    website = fields.Str()

    phone = fields.Str()

    country = fields.Str()

    state = fields.Str()

    city = fields.Str()

    address = fields.Str()

    is_active = fields.Bool()

    created_at = fields.DateTime()

    updated_at = fields.DateTime()
