from marshmallow import Schema, fields


class SignupSchema(Schema):

    full_name = fields.String(required=True)

    email = fields.Email(required=True)

    password = fields.String(required=True)


class LoginSchema(Schema):

    email = fields.Email(required=True)

    password = fields.String(required=True)