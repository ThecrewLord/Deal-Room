from marshmallow import Schema, fields, validate

from app.constants.poc_outcome import POC_OUTCOMES


class PocRequestSchema(Schema):
    opportunity_id = fields.Int(required=True)
    poc_name = fields.Str(required=True, validate=validate.Length(min=2, max=150))
    objective = fields.Str(required=True, validate=validate.Length(min=1))
    success_metric = fields.Str(required=True, validate=validate.Length(min=1))
    exit_criteria = fields.Str(required=True, validate=validate.Length(min=1))
    target_date = fields.Date(required=True)
    failure_condition = fields.Str(required=True, validate=validate.Length(min=1))
    remarks = fields.Str(allow_none=True)


class PocDesignUpdateSchema(Schema):
    poc_name = fields.Str(validate=validate.Length(min=2, max=150))
    objective = fields.Str()
    success_metric = fields.Str()
    exit_criteria = fields.Str()
    target_date = fields.Date()
    failure_condition = fields.Str()
    remarks = fields.Str(allow_none=True)
    updated_at = fields.DateTime(required=True)


class PocApprovalSchema(Schema):
    updated_at = fields.DateTime(required=True)


class PocRejectionSchema(Schema):
    reason = fields.Str(required=True, validate=validate.Length(min=1, max=2000))
    updated_at = fields.DateTime(required=True)


class PocExecutionStartSchema(Schema):
    updated_at = fields.DateTime(required=True)


class PocResultSchema(Schema):
    execution_status = fields.Str(required=True, validate=validate.OneOf(
        ["In Progress", "Submitted", "Completed", "Failed", "Abandoned"]
    ))
    poc_access_link = fields.Str(required=True, validate=validate.Length(min=1))
    outcome = fields.Str(required=True, validate=validate.OneOf(POC_OUTCOMES))
    outcome_notes = fields.Str(required=True, validate=validate.Length(min=1))
    remarks = fields.Str(allow_none=True)
    updated_at = fields.DateTime(required=True)


class PocCompleteSchema(Schema):
    updated_at = fields.DateTime(required=True)


class PocUserSummarySchema(Schema):
    user_id = fields.Int()
    full_name = fields.Str()


class PocResponseSchema(Schema):
    poc_id = fields.Int()
    opportunity_id = fields.Int()
    poc_name = fields.Str()
    start_date = fields.Date()
    end_date = fields.Date()
    status = fields.Str()
    remarks = fields.Str(allow_none=True)
    objective = fields.Str()
    success_metric = fields.Str()
    exit_criteria = fields.Str(allow_none=True)
    target_date = fields.Date()
    failure_condition = fields.Str()
    stakeholder_signoff = fields.Bool()
    outcome = fields.Str(allow_none=True)
    outcome_notes = fields.Str(allow_none=True)
    poc_access_link = fields.Str(allow_none=True)
    requested_by = fields.Int(allow_none=True)
    requester = fields.Nested(PocUserSummarySchema, allow_none=True)
    approved_by = fields.Int(allow_none=True)
    approver = fields.Nested(PocUserSummarySchema, allow_none=True)
    approved_at = fields.DateTime(allow_none=True)
    rejection_reason = fields.Str(allow_none=True)
    submitted_by = fields.Int(allow_none=True)
    submitter = fields.Nested(PocUserSummarySchema, allow_none=True)
    submitted_at = fields.DateTime(allow_none=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
