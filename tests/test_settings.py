from src.utils.settings import (
    get_minimum_required_signals,
    get_required_categories,
    load_settings,
)


def test_load_settings():
    settings = load_settings()

    assert set(settings) == {"engine"}


def test_get_required_categories():
    categories = get_required_categories()

    assert "Liquidity Condition" in categories
    assert "Holder Condition" in categories
    assert "Blockspace / Network Demand" in categories


def test_get_minimum_required_signals():
    minimum_required_signals = get_minimum_required_signals()

    assert minimum_required_signals == 4
