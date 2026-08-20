from marshmallow import Schema, fields


class StageResponseSchema(Schema):

    stage_id = fields.Int()

    stage_name = fields.Str()

    display_order = fields.Int()

    requires_poc = fields.Bool()

    is_closed = fields.Bool()

    is_won = fields.Bool()
