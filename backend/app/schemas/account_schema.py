from marshmallow import Schema, fields, validate


class AccountCreateSchema(Schema):
    account_name = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=200),
    )
