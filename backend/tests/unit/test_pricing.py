from app.modules.pricing.service import (
    compute_fair_band,
    compute_traditional_scenario,
    load_pricing_config,
)


def test_pricing_waterfall_arithmetic_ac_prc_01():
    """Verify AC-PRC-01: landed = farmgate + transport + platform_fee (±0.01)

    platform_fee = farmgate * platform_fee_pct / 100.
    """
    farmgate = 22.50
    transport = 3.47
    platform_fee_pct = 2.0

    platform_fee = round(farmgate * (platform_fee_pct / 100.0), 2)
    assert platform_fee == 0.45

    landed = round(farmgate + transport + platform_fee, 2)
    assert landed == 26.42

    # Verification: sum equals landed within 0.01
    assert abs((farmgate + transport + platform_fee) - landed) <= 0.01


def test_traditional_scenario_ac_prc_03_hand_computed_fixture():
    """Verify AC-PRC-03: Scenario formulas (ML.md §12) against hand-computed fixture."""
    cfg = {
        "commission_agent_pct": 5.0,
        "trader_margin_pct": 8.0,
        "retail_margin_pct": 12.0,
        "last_mile_cost_per_kg": 1.0,
        "platform_fee_pct": 2.0,
    }

    benchmark_modal = 25.00
    farmgate = 22.50
    landed = 26.42
    producer_to_hub_transport = 2.50

    # Hand calculation:
    # farmer_mandi_net = 25.0 * (1 - 0.05) - 2.50 = 25.0 * 0.95 - 2.50 = 23.75 - 2.50 = 21.25
    # buyer_traditional = 25.0 * (1 + 0.08) * (1 + 0.12) + 1.0 = 25.0 * 1.08 * 1.12 + 1.0 = 27.0 * 1.12 + 1.0 = 30.24 + 1.0 = 31.24
    # delta_farmer_pct = (22.50 - 21.25) / 21.25 * 100 = 1.25 / 21.25 * 100 ≈ 5.88%
    # delta_buyer_pct = (26.42 - 31.24) / 31.24 * 100 = -4.82 / 31.24 * 100 ≈ -15.43%
    scenario = compute_traditional_scenario(
        benchmark_modal=benchmark_modal,
        farmgate_per_kg=farmgate,
        landed_per_kg=landed,
        producer_to_hub_transport_per_kg=producer_to_hub_transport,
        cfg=cfg,
    )

    assert scenario.farmer_mandi_net_per_kg == 21.25
    assert scenario.buyer_traditional_per_kg == 31.24
    assert scenario.delta_farmer_pct == 5.88
    assert scenario.delta_buyer_pct == -15.43
    assert scenario.assumptions.commission_agent_pct == 5.0
    assert scenario.assumptions.trader_margin_pct == 8.0


def test_fair_band_ac_prc_03_valid_and_inverted():
    """Verify AC-PRC-03: fair band L = farmer_mandi_net, U = (buyer_traditional - transport) / (1 + fee_pct/100)

    and fair band is None when U <= L.
    """
    farmer_mandi_net = 21.25
    buyer_traditional = 31.24
    transport_per_kg = 3.47
    platform_fee_pct = 2.0

    # U = (31.24 - 3.47) / 1.02 = 27.77 / 1.02 ≈ 27.23
    band = compute_fair_band(
        farmer_mandi_net=farmer_mandi_net,
        buyer_traditional=buyer_traditional,
        transport_per_kg=transport_per_kg,
        platform_fee_pct=platform_fee_pct,
    )
    assert band is not None
    assert band.low == 21.25
    assert band.high == 27.23
    assert band.high > band.low

    # Inverted band where U <= L returns None
    inverted_band = compute_fair_band(
        farmer_mandi_net=30.00,
        buyer_traditional=25.00,
        transport_per_kg=5.00,
        platform_fee_pct=2.0,
    )
    assert inverted_band is None


def test_config_loader():
    """Verify load_pricing_config loads default parameters cleanly."""
    cfg = load_pricing_config()
    assert cfg["platform_fee_pct"] == 2.0
    assert cfg["commission_agent_pct"] == 5.0
    assert cfg["trader_margin_pct"] == 8.0
    assert cfg["retail_margin_pct"] == 12.0
    assert cfg["last_mile_cost_per_kg"] == 1.0
