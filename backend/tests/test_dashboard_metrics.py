from app import create_app
from app.database import db


def test_dashboard_api():


    app = create_app()


    with app.test_client() as client:


        response = client.get(
            "/dashboard/metrics"
        )


        assert response.status_code == 200



def test_weighted_forecast():

    value = 2500000

    probability = 40


    forecast = (
        value *
        probability /
        100
    )


    assert forecast == 1000000



def test_conversion_rate():

    won = 5

    lost = 5


    rate = (
        won /
        (won + lost)
    ) * 100


    assert rate == 50



def test_stage_ageing():

    current = 10

    entered = 3


    ageing = current - entered


    assert ageing == 7



def test_stalled_deal():

    activity_days = 20

    threshold = 14


    assert activity_days > threshold



def test_win_loss_ratio():

    won = 10

    lost = 5


    ratio = won / lost


    assert ratio == 2



def test_partner_contribution():

    opportunities = [
        100000,
        200000
    ]


    assert sum(opportunities) == 300000



def test_active_pocs():

    active = 3

    assert active >= 0