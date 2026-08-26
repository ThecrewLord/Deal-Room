from marshmallow import Schema, fields


class DashboardSchema(Schema):

    total_opportunities = fields.Int()

    total_pipeline_value = fields.Float()

    weighted_forecast = fields.Float()

    open_opportunities = fields.Int()

    closed_won = fields.Int()

    closed_lost = fields.Int()

    conversion_rate = fields.Float()

    stage_ageing = fields.List(
        fields.Dict()
    )

    average_stage_ageing = fields.Float()

    stalled_deals = fields.Int()

    active_pocs = fields.Int()

    win_loss_ratio = fields.Float()

    partner_contribution = fields.Int()

    pipeline_by_stage = fields.List(
        fields.Dict()
    )

    recent_opportunities = fields.List(
        fields.Dict()
    )

    upcoming_pocs = fields.List(
        fields.Dict()
    )

    recent_activity = fields.List(
        fields.Dict()
    )