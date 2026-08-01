from marshmallow import Schema, fields, validate


class OpportunityCreateSchema(Schema):

    account_id = fields.Int(required=True)

    stage_id = fields.Int(required=True)

    opportunity_name = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=200),
    )

    description = fields.Str()

    estimated_value = fields.Decimal()

    probability = fields.Int()

    expected_close_date = fields.Date()

    status = fields.Str()


class OpportunityUpdateSchema(Schema):

    account_id = fields.Int()

    stage_id = fields.Int()

    opportunity_name = fields.Str(
        validate=validate.Length(min=2, max=200),
    )

    description = fields.Str()

    estimated_value = fields.Decimal()

    probability = fields.Int()

    expected_close_date = fields.Date()

    status = fields.Str()

    updated_at = fields.DateTime(required=True)


class OpportunityResponseSchema(Schema):

    opportunity_id = fields.Int()

    account_id = fields.Int()

    stage_id = fields.Int()

    opportunity_name = fields.Str()

    description = fields.Str()

    estimated_value = fields.Decimal()

    probability = fields.Int()

    expected_close_date = fields.Date()

    status = fields.Str()

    is_active = fields.Bool()

    created_at = fields.DateTime()

    updated_at = fields.DateTime()