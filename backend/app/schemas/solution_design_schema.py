from marshmallow import Schema, fields


class SolutionDesignUpdateSchema(Schema):
    solution_summary = fields.Str(allow_none=True)
    technical_approach = fields.Str(allow_none=True)
    technical_requirements = fields.Str(allow_none=True)
    architecture_notes = fields.Str(allow_none=True)
    risks = fields.Str(allow_none=True)
    assumptions = fields.Str(allow_none=True)
    updated_at = fields.DateTime(required=True)


class SolutionDesignResponseSchema(Schema):
    design_id = fields.Int()
    opportunity_id = fields.Int()
    solution_summary = fields.Str(allow_none=True)
    technical_approach = fields.Str(allow_none=True)
    technical_requirements = fields.Str(allow_none=True)
    architecture_notes = fields.Str(allow_none=True)
    risks = fields.Str(allow_none=True)
    assumptions = fields.Str(allow_none=True)
    updated_at = fields.DateTime()
    created_at = fields.DateTime()
