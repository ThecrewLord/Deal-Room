from marshmallow import Schema, fields, validate


class PocCreateSchema(Schema):

    opportunity_id = fields.Int(required=True)

    poc_name = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=150),
    )

    start_date = fields.Date()

    end_date = fields.Date()

    status = fields.Str()

    remarks = fields.Str()

    # --- Mandatory exit-criteria fields ---

    objective = fields.Str(required=True)

    success_metric = fields.Str(required=True)

    target_date = fields.Date(required=True)

    failure_condition = fields.Str(required=True)

    stakeholder_signoff = fields.Bool(required=True)


class PocUpdateSchema(Schema):

    poc_name = fields.Str(
        validate=validate.Length(min=2, max=150),
    )

    start_date = fields.Date()

    end_date = fields.Date()

    status = fields.Str()

    remarks = fields.Str()

    objective = fields.Str()

    success_metric = fields.Str()

    target_date = fields.Date()

    failure_condition = fields.Str()

    stakeholder_signoff = fields.Bool()

    outcome = fields.Str(
        validate=validate.OneOf(
            ["Success", "Failure", "Ongoing", "Abandoned"]
        ),
    )

    outcome_notes = fields.Str()

    updated_at = fields.DateTime(required=True)


class PocResponseSchema(Schema):

    poc_id = fields.Int()

    opportunity_id = fields.Int()

    poc_name = fields.Str()

    start_date = fields.Date()

    end_date = fields.Date()

    status = fields.Str()

    remarks = fields.Str()

    objective = fields.Str()

    success_metric = fields.Str()

    target_date = fields.Date()

    failure_condition = fields.Str()

    stakeholder_signoff = fields.Bool()

    outcome = fields.Str()

    outcome_notes = fields.Str()

    created_at = fields.DateTime()

    updated_at = fields.DateTime()