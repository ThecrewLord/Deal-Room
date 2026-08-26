from marshmallow import Schema, fields, validate


class UserSummarySchema(Schema):
    user_id = fields.Int()
    full_name = fields.Str()


class StageSummarySchema(Schema):
    stage_id = fields.Int()
    stage_name = fields.Str()
    display_order = fields.Int()
    requires_poc = fields.Bool()
    is_closed = fields.Bool()
    is_won = fields.Bool()


class OpportunityTeamMemberSchema(Schema):
    team_id = fields.Int()
    user_id = fields.Int()
    role = fields.Str()
    user = fields.Nested(UserSummarySchema, allow_none=True)


class OpportunityCreateSchema(Schema):
    # Only client-owned creation fields are accepted.
    account_id = fields.Int(required=True)
    opportunity_name = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=200),
    )
    description = fields.Str(allow_none=True)
    estimated_value = fields.Decimal(allow_none=True)
    probability = fields.Int(allow_none=True, validate=validate.Range(min=0, max=100))
    expected_close_date = fields.Date(allow_none=True)


class OpportunityUpdateSchema(Schema):
    # Stage, status, account, creator and sales owner are server-controlled.
    opportunity_name = fields.Str(
        validate=validate.Length(min=2, max=200),
    )
    description = fields.Str(allow_none=True)
    estimated_value = fields.Decimal(allow_none=True)
    probability = fields.Int(allow_none=True, validate=validate.Range(min=0, max=100))
    expected_close_date = fields.Date(allow_none=True)
    updated_at = fields.DateTime(required=True)


class OpportunityResponseSchema(Schema):
    opportunity_id = fields.Int()
    account_id = fields.Int()
    account_name = fields.Method("get_account_name")
    created_by = fields.Int(allow_none=True)
    sales_owner_id = fields.Int(allow_none=True)

    created_by_user = fields.Nested(UserSummarySchema, allow_none=True)
    sales_owner = fields.Nested(UserSummarySchema, allow_none=True)

    stage_id = fields.Int()
    current_stage = fields.Nested(StageSummarySchema, allow_none=True)

    opportunity_name = fields.Str()
    description = fields.Str(allow_none=True)
    estimated_value = fields.Decimal(allow_none=True)
    probability = fields.Int(allow_none=True)
    expected_close_date = fields.Date(allow_none=True)

    status = fields.Str()
    lifecycle_state = fields.Str(allow_none=True)
    is_active = fields.Bool()

    team_members = fields.Nested(
        OpportunityTeamMemberSchema,
        many=True,
    )

    created_at = fields.DateTime()
    updated_at = fields.DateTime()

    def get_account_name(self, obj):
        return obj.account.account_name if getattr(obj, "account", None) else None


class StageHistoryResponseSchema(Schema):
    history_id = fields.Int()
    opportunity_id = fields.Int()
    stage_id = fields.Int()
    stage = fields.Nested(StageSummarySchema, allow_none=True)
    changed_by = fields.Int(allow_none=True)
    user = fields.Nested(UserSummarySchema, allow_none=True)
    remarks = fields.Str(allow_none=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class OpportunityReviewSchema(Schema):
    decision = fields.Str(required=True, validate=validate.OneOf(["APPROVE", "REJECT"]))
    sales_owner_id = fields.Int(allow_none=True)
    reason = fields.Str(allow_none=True, validate=validate.Length(max=2000))
    updated_at = fields.DateTime(required=True)


class PreSalesAssignmentSchema(Schema):
    solution_engineer_ids = fields.List(
        fields.Int(),
        required=True,
        validate=validate.Length(min=1),
    )
    delivery_ids = fields.List(
        fields.Int(),
        required=False,
        load_default=list,
    )
    updated_at = fields.DateTime(required=True)

class TechnicalStageTransitionSchema(Schema):
    target_stage = fields.Str(required=True)
    remarks = fields.Str(allow_none=True)
    updated_at = fields.DateTime(required=True)


class OpportunityCloseSchema(Schema):
    reason = fields.Str(allow_none=True, validate=validate.Length(max=2000))
    updated_at = fields.DateTime(required=True)
