from decimal import Decimal

from marshmallow import Schema, ValidationError, fields, validate


def _money(value):
    value = Decimal(str(value))
    if not value.is_finite():
        raise ValidationError("Value must be finite.")
    if value < 0:
        raise ValidationError("Value must be non-negative.")
    if value.as_tuple().exponent < -2:
        raise ValidationError("Value supports at most 2 decimal places.")
    if value >= Decimal("10000000000000"):
        raise ValidationError("Value exceeds the supported precision.")
    return value



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
    pain_points = fields.Str(allow_none=True)
    estimated_value = fields.Decimal(required=True, validate=_money)
    probability = fields.Int(allow_none=True, validate=validate.Range(min=0, max=100))
    expected_close_date = fields.Date(allow_none=True)


class OpportunityUpdateSchema(Schema):
    # Stage, status, account, creator and sales owner are server-controlled.
    opportunity_name = fields.Str(
        validate=validate.Length(min=2, max=200),
    )
    description = fields.Str(allow_none=True)
    pain_points = fields.Str(allow_none=True)
    probability = fields.Int(allow_none=True, validate=validate.Range(min=0, max=100))
    expected_close_date = fields.Date(allow_none=True)
    expected_version = fields.Int(required=True, validate=validate.Range(min=1))


class OpportunityValueChangeSchema(Schema):
    new_value = fields.Decimal(required=True, validate=_money)
    reason = fields.Str(required=True, validate=validate.Length(min=1, max=2000))
    expected_version = fields.Int(required=True, validate=validate.Range(min=1))


class ClosedWonRequestResponseSchema(Schema):
    request_id = fields.Int()
    opportunity_id = fields.Int()
    requested_by = fields.Int()
    requested_active_role = fields.Str()
    status = fields.Str()
    resolved_by = fields.Int(allow_none=True)
    resolved_active_role = fields.Str(allow_none=True)
    resolution_reason = fields.Str(allow_none=True)
    requested_at = fields.DateTime()
    resolved_at = fields.DateTime(allow_none=True)


class OpportunityResponseSchema(Schema):
    opportunity_id = fields.Int()
    account_id = fields.Int()
    account_name = fields.Method("get_account_name")
    created_by = fields.Int(allow_none=True)
    deal_finder_id = fields.Method("get_deal_finder_id")
    deal_finder = fields.Method("get_deal_finder")
    sales_owner_id = fields.Int(allow_none=True)

    created_by_user = fields.Nested(UserSummarySchema, allow_none=True)
    sales_owner = fields.Nested(UserSummarySchema, allow_none=True)

    stage_id = fields.Int()
    current_stage = fields.Nested(StageSummarySchema, allow_none=True)
    lifecycle_stage = fields.Str()
    outcome = fields.Str()
    operational_status = fields.Str()
    review_status = fields.Str()
    row_version = fields.Int()
    lost_reason = fields.Str(allow_none=True)
    lost_explanation = fields.Str(allow_none=True)

    opportunity_name = fields.Str()
    description = fields.Str(allow_none=True)
    pain_points = fields.Str(allow_none=True)
    estimated_value = fields.Decimal(allow_none=True)
    final_revenue = fields.Decimal(allow_none=True)
    closed_won_request = fields.Nested(ClosedWonRequestResponseSchema, allow_none=True)
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

    def get_deal_finder_id(self, obj):
        # created_by is the persisted immutable Deal Finder field.
        return obj.created_by

    def get_deal_finder(self, obj):
        user = getattr(obj, "created_by_user", None)
        if not user:
            return None
        return {"user_id": user.user_id, "full_name": user.full_name}


class OpportunityValueHistoryResponseSchema(Schema):
    history_id = fields.Int()
    opportunity_id = fields.Int()
    old_value = fields.Decimal(allow_none=True)
    new_value = fields.Decimal()
    reason = fields.Str()
    actor_id = fields.Int()
    actor_active_role = fields.Str()
    changed_at = fields.DateTime()
    opportunity_row_version = fields.Int()
    actor = fields.Nested(UserSummarySchema, allow_none=True)


class StageHistoryResponseSchema(Schema):
    history_id = fields.Int()
    opportunity_id = fields.Int()
    stage_id = fields.Int()
    stage = fields.Nested(StageSummarySchema, allow_none=True)
    changed_by = fields.Int(allow_none=True)
    user = fields.Nested(UserSummarySchema, allow_none=True)
    from_lifecycle_stage = fields.Str(allow_none=True)
    to_lifecycle_stage = fields.Str(allow_none=True)
    actor_active_role = fields.Str(allow_none=True)
    version = fields.Int(allow_none=True)
    remarks = fields.Str(allow_none=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class OpportunityReviewSchema(Schema):
    decision = fields.Str(required=True, validate=validate.OneOf(["APPROVE", "REJECT"]))
    sales_owner_id = fields.Int(allow_none=True)
    reason = fields.Str(allow_none=True, validate=validate.Length(max=2000))
    opportunity_name = fields.Str(allow_none=True, validate=validate.Length(min=2, max=200))
    description = fields.Str(allow_none=True)
    pain_points = fields.Str(allow_none=True)
    probability = fields.Int(allow_none=True, validate=validate.Range(min=0, max=100))
    expected_close_date = fields.Date(allow_none=True)
    expected_version = fields.Int(required=True, validate=validate.Range(min=1))


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

class OpportunityCloseSchema(Schema):
    reason = fields.Str(allow_none=True, validate=validate.Length(max=2000))
    explanation = fields.Str(allow_none=True, validate=validate.Length(max=5000))
    expected_version = fields.Int(required=True, validate=validate.Range(min=1))


class ClosedWonRequestSchema(Schema):
    expected_version = fields.Int(required=True, validate=validate.Range(min=1))


class ClosedWonRequestResolutionSchema(Schema):
    expected_version = fields.Int(required=True, validate=validate.Range(min=1))
    reason = fields.Str(allow_none=True, validate=validate.Length(max=2000))


class OpportunityStatusSchema(Schema):
    expected_version = fields.Int(required=True, validate=validate.Range(min=1))
    status = fields.Str(required=True, validate=validate.OneOf(["Active", "Stalled"]))
