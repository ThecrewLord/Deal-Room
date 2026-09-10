from marshmallow import Schema, fields, validate


ALLOWED_STAKEHOLDER_TAGS = [
    "Economic Buyer",
    "Technical Champion",
    "End User",
    "Blocker",
    "Decision Maker",
]


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

    updated_at = fields.DateTime()


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


class StakeholderTagCreateSchema(Schema):

    tag = fields.Str(
        required=True,
        validate=validate.OneOf(ALLOWED_STAKEHOLDER_TAGS),
    )


class StakeholderTagResponseSchema(Schema):

    stakeholder_tag_id = fields.Int()

    stakeholder_id = fields.Int()

    opportunity_id = fields.Int()

    tag = fields.Str()

    created_at = fields.DateTime()

    updated_at = fields.DateTime()