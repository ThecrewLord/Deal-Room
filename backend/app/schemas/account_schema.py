from marshmallow import Schema, fields, validate
class AccountCreateSchema(Schema):
    account_name=fields.Str(required=True,validate=validate.Length(min=2,max=200))
    industry=fields.Str(allow_none=True); website=fields.Str(allow_none=True); phone=fields.Str(allow_none=True)
    country=fields.Str(allow_none=True); state=fields.Str(allow_none=True); city=fields.Str(allow_none=True); address=fields.Str(allow_none=True)
