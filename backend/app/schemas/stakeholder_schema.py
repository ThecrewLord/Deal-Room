from marshmallow import Schema, fields, validate

PHONE_PATTERN = r"^\d{10}$"

TAGS = [
    "Economic Buyer",
    "Technical Champion",
    "End User",
    "Blocker",
    "Decision Maker",
]


class StakeholderCreateSchema(Schema):
    opportunity_id = fields.Int(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=150))
    job_title = fields.Str(allow_none=True)
    email = fields.Email(allow_none=True)
    phone = fields.Str(
        allow_none=True,
        validate=validate.Regexp(
            PHONE_PATTERN,
            error="Phone number must contain exactly 10 digits.",
        ),
    )
    company = fields.Str(allow_none=True)
    tags = fields.List(
        fields.Str(validate=validate.OneOf(TAGS)),
        load_default=list,
    )
    notes = fields.Str(allow_none=True)


class StakeholderUpdateSchema(Schema):
    # Uses the parent opportunity's row_version because stakeholder mutations
    # change shared deal context and share its optimistic-concurrency boundary.
    expected_version = fields.Int(required=True, validate=validate.Range(min=1))
    name = fields.Str(validate=validate.Length(min=1, max=150))
    job_title = fields.Str(allow_none=True)
    email = fields.Email(allow_none=True)
    phone = fields.Str(
        allow_none=True,
        validate=validate.Regexp(
            PHONE_PATTERN,
            error="Phone number must contain exactly 10 digits.",
        ),
    )
    company = fields.Str(allow_none=True)
    tags = fields.List(fields.Str(validate=validate.OneOf(TAGS)))
    notes = fields.Str(allow_none=True)
    updated_at = fields.DateTime(allow_none=True)


class StakeholderResponseSchema(Schema):
    stakeholder_id = fields.Int()
    opportunity_id = fields.Int()
    opportunity_version = fields.Method("get_opportunity_version")

    opportunity_name = fields.Method("get_opportunity_name")

    name = fields.Str()
    job_title = fields.Str(allow_none=True)
    email = fields.Str(allow_none=True)
    phone = fields.Str(allow_none=True)
    company = fields.Str(allow_none=True)
    is_decision_maker = fields.Bool()
    tags = fields.Method("get_tags")
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

    def get_tags(self, obj):
        return [t.name for t in obj.tags]

    def get_opportunity_version(self, obj):
        return obj.opportunity.row_version if obj.opportunity else None

    def get_opportunity_name(self, obj):
        return (
            obj.opportunity.opportunity_name
            if obj.opportunity
            else "Unknown Opportunity"
        )
