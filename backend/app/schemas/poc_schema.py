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



class PocExecutionStartSchema(Schema):
    updated_at = fields.DateTime(required=True)


class PocResultSchema(Schema):
    execution_status = fields.Str(required=True, validate=validate.OneOf(
        ["Submitted"]
    ))
    outcome = fields.Str(required=True, validate=validate.OneOf(POC_OUTCOMES))
    outcome_notes = fields.Str(load_default="", allow_none=True)
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
    outcome = fields.Str(allow_none=True)
    outcome_notes = fields.Str(allow_none=True)
    requested_by = fields.Int(allow_none=True)
    requester = fields.Nested(PocUserSummarySchema, allow_none=True)
    submitted_by = fields.Int(allow_none=True)
    submitter = fields.Nested(PocUserSummarySchema, allow_none=True)
    submitted_at = fields.DateTime(allow_none=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
