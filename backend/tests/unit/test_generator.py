from datetime import timedelta

import pandas as pd

from ml.generate_data import generate_panels, load_generator_config


def test_generator_complete_panel_dimensions():
    """Verify complete pre-dropout panel has exactly 18,250 rows and post-dropout preserves all series."""
    config = load_generator_config()
    complete_df, post_drop_df, _ = generate_panels(config=config, seed=42)

    # 1. Exactly 5 hubs × 5 crops × 730 days = 18,250
    assert len(complete_df) == 18250

    # 2. Pre-dropout coverage
    assert complete_df["hub_id"].nunique() == 5
    assert complete_df["crop_id"].nunique() == 5
    assert complete_df["date"].nunique() == 730

    # 3. Post-dropout representation: all 5 hubs and 5 crops must still be represented
    assert post_drop_df["hub_id"].nunique() == 5
    assert post_drop_df["crop_id"].nunique() == 5

    # Dropout rate should be around 1% (between 0.5% and 1.5%)
    dropout_rate = (len(complete_df) - len(post_drop_df)) / len(complete_df)
    assert 0.005 <= dropout_rate <= 0.015


def test_generator_reproducibility():
    """Verify generator is strictly reproducible: identical count, values, ordering, and data."""
    config = load_generator_config()

    comp1, post1, prices1 = generate_panels(config=config, seed=42)
    comp2, post2, prices2 = generate_panels(config=config, seed=42)

    # Check complete panel
    assert len(comp1) == len(comp2)
    pd.testing.assert_frame_equal(comp1, comp2)

    # Check post-dropout dataset
    assert len(post1) == len(post2)
    pd.testing.assert_frame_equal(post1, post2)

    # Check synthetic prices
    assert len(prices1) == len(prices2)
    pd.testing.assert_frame_equal(prices1, prices2)


def test_generator_positive_values():
    """Verify all demand and price numbers are strictly positive."""
    config = load_generator_config()
    complete_df, post_drop_df, _ = generate_panels(config=config, seed=42)

    assert (complete_df["demand_kg"] > 0).all()
    assert (complete_df["avg_price_per_kg"] > 0).all()
    assert (post_drop_df["demand_kg"] > 0).all()
    assert (post_drop_df["avg_price_per_kg"] > 0).all()


def test_generator_price_anchoring():
    """Verify DEMO-PRICE-ANCHOR: last 30 days of prices for every crop are within ±10% of base price."""
    config = load_generator_config()
    complete_df, _, _ = generate_panels(config=config, seed=42)

    base_prices = config["base_prices"]
    max_date = complete_df["date"].max()
    anchor_start = max_date - timedelta(days=29)

    last_30_days_df = complete_df[complete_df["date"] >= anchor_start]
    assert last_30_days_df["date"].nunique() == 30

    for crop_name, base_p in base_prices.items():
        crop_rows = last_30_days_df[last_30_days_df["crop_name"] == crop_name]
        min_allowed = round(base_p * 0.90, 2)
        max_allowed = round(base_p * 1.10, 2)

        actual_min = crop_rows["avg_price_per_kg"].min()
        actual_max = crop_rows["avg_price_per_kg"].max()

        assert actual_min >= min_allowed - 0.05, f"{crop_name} min price {actual_min} below {min_allowed}"
        assert actual_max <= max_allowed + 0.05, f"{crop_name} max price {actual_max} above {max_allowed}"


def test_generator_synthetic_benchmark_prices():
    """Verify synthetic daily benchmark prices for last 90 days."""
    config = load_generator_config()
    _, _, prices_df = generate_panels(config=config, seed=42)

    # 5 hubs × 5 crops × 90 days = 2250 rows
    assert len(prices_df) == 2250
    assert prices_df["hub_id"].nunique() == 5
    assert prices_df["crop_id"].nunique() == 5
    assert prices_df["price_date"].nunique() == 90

    # Validation: min <= modal <= max
    assert (prices_df["min_price_per_kg"] <= prices_df["modal_price_per_kg"]).all()
    assert (prices_df["modal_price_per_kg"] <= prices_df["max_price_per_kg"]).all()

    # Integrity attributes
    assert (prices_df["source"] == "SYNTHETIC_DEMO").all()
    assert prices_df["is_synthetic"].all()
