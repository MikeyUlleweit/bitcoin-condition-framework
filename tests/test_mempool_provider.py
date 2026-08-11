import pytest

from src.providers.mempool import get_mempool_summary, get_recommended_fees

pytestmark = pytest.mark.live


def test_get_recommended_fees_returns_expected_keys():
    fees = get_recommended_fees()

    assert "fastestFee" in fees
    assert "halfHourFee" in fees
    assert "hourFee" in fees
    assert "minimumFee" in fees

    for value in fees.values():
        assert isinstance(value, int)
        assert value >= 0


def test_get_mempool_summary_returns_numeric_values():
    summary = get_mempool_summary()

    assert "count" in summary
    assert "vsize" in summary
    assert "total_fee" in summary

    for value in summary.values():
        assert isinstance(value, int | float)
        assert value >= 0
