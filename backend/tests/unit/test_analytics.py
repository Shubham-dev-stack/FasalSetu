from datetime import date
from unittest.mock import MagicMock

from app.db.models import (
    Crop,
    DemandHub,
    Listing,
    ProducerProfile,
)
from app.modules.analytics.service import (
    get_analytics_overview,
    get_analytics_supply_demand,
)


def test_analytics_overview_empty_db_ac_anl_03():
    """AC-ANL-03: Empty database returns zero counts, null ratios/averages, HTTP 200 equivalent."""
    mock_db = MagicMock()

    # Query mock: when filtering Order, Requirement, RoutePlan, Shipment, DemandHub
    # Return empty lists
    def query_side_effect(model):
        m = MagicMock()
        m.filter.return_value.all.return_value = []
        m.filter.return_value.first.return_value = None
        m.order_by.return_value.all.return_value = []
        m.all.return_value = []
        m.first.return_value = None
        return m

    mock_db.query.side_effect = query_side_effect

    res = get_analytics_overview(mock_db)
    assert res.kpis.committed_orders == 0
    assert res.kpis.committed_volume_kg == 0.0
    assert res.kpis.committed_value_inr == 0.0
    assert res.kpis.requirement_fill_rate_pct is None
    assert res.kpis.avg_logistics_cost_per_kg is None
    assert res.kpis.route_savings_km == 0.0
    assert res.kpis.route_savings_inr == 0.0
    assert res.kpis.avg_utilization_pct is None

    assert res.price_gap.orders_considered == 0
    assert res.price_gap.avg_farmer_delta_pct is None
    assert res.price_gap.avg_buyer_delta_pct is None
    assert res.price_gap.basis == "MODELLED_SCENARIO"

    assert len(res.daily) == 14
    for pt in res.daily:
        assert pt.orders == 0
        assert pt.volume_kg == 0.0


def test_analytics_supply_demand_attribution_no_double_counting(monkeypatch):
    """Verify Rule D-026: Active produce is attributed to exactly one nearest hub."""
    mock_db = MagicMock()

    hub1 = DemandHub(id=1, name="Hub 1", lat=28.70, lng=77.10)
    hub2 = DemandHub(id=2, name="Hub 2", lat=28.40, lng=77.30)
    crop1 = Crop(id=1, name="Tomato")

    # Producer near Hub 1
    prod1 = ProducerProfile(id=1, lat=28.71, lng=77.11)
    listing1 = Listing(
        id=1,
        producer_id=1,
        crop_id=1,
        status="ACTIVE",
        available_until=date(2030, 1, 1),
        quantity_available_kg=500.0,
    )
    listing1.producer = prod1

    def query_side_effect(model):
        m = MagicMock()
        if model is DemandHub:
            m.order_by.return_value.all.return_value = [hub1, hub2]
            m.all.return_value = [hub1, hub2]
        elif model is Crop:
            m.order_by.return_value.all.return_value = [crop1]
            m.filter.return_value.first.return_value = crop1
            m.all.return_value = [crop1]
        elif model is Listing:
            m_join = MagicMock()
            m_join.filter.return_value.all.return_value = [listing1]
            m.join.return_value = m_join
        else:
            m.filter.return_value.all.return_value = []
            m.all.return_value = []
        return m

    mock_db.query.side_effect = query_side_effect

    # Mock get_demand_forecast to return dummy forecast
    monkeypatch.setattr(
        "app.modules.analytics.service.get_demand_forecast",
        lambda db, hub_id, crop_id, horizon_days: {
            "forecast": [{"point_forecast_kg": 100.0} for _ in range(horizon_days)]
        },
    )

    res = get_analytics_supply_demand(mock_db)
    assert len(res.rows) == 2  # Hub1 x Crop1, Hub2 x Crop1

    row_h1 = next(r for r in res.rows if r.hub_id == 1)
    row_h2 = next(r for r in res.rows if r.hub_id == 2)

    # Hub 1 got all 500 kg, Hub 2 got 0 kg (no double counting)
    assert row_h1.supply_kg == 500.0
    assert row_h2.supply_kg == 0.0
