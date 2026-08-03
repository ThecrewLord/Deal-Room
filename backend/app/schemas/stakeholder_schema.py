from marshmallow import Schema, fields, validate


class StakeholderCreateSchema(Schema):

    opportunity_id = fields.Int(required=True)

    stakeholder_name = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=150),
    )

    designation = fields.Str()

    email = fields.Email()

    phone = fields.Str()

    influence_level = fields.Str(
        validate=validate.OneOf(
            ["Decision Maker", "Influencer", "User", "Blocker"]
        ),
    )

    notes = fields.Str()


class StakeholderUpdateSchema(Schema):

    stakeholder_name = fields.Str(
        validate=validate.Length(min=2, max=150),
    )

    designation = fields.Str()

    email = fields.Email()

    phone = fields.Str()

    influence_level = fields.Str(
        validate=validate.OneOf(
            ["Decision Maker", "Influencer", "User", "Blocker"]
        ),
    )

    notes = fields.Str()

    updated_at = fields.DateTime(required=True)


class StakeholderResponseSchema(Schema):

    stakeholder_id = fields.Int()

    opportunity_id = fields.Int()

    stakeholder_name = fields.Str()

    designation = fields.Str()

    email = fields.Str()

    phone = fields.Str()

    influence_level = fields.Str()

    notes = fields.Str()

    created_at = fields.DateTime()

    updated_at = fields.DateTime()
