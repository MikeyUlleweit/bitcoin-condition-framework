from datetime import UTC, datetime

import pytest

from src.models.liquidity import LiquidityObservation
from src.models.observation import MetricObservation
from src.models.signal import CalibrationStatus, SourceStatus
from src.signals.liquidity_signal import evaluate_liquidity


def test_evaluate_liquidity_keeps_defi_tvl_as_unscored_context() -> None:
    observation = LiquidityObservation(
        source="DeFiLlama",
        observed_at=None,
        retrieved_at=datetime(2026, 8, 11, 18, 30, tzinfo=UTC),
        defi_tvl=MetricObservation.available(65_000_000_000, "USD"),
        chain_count=2,
        valid_chain_count=2,
        invalid_chain_count=0,
    )

    signal = evaluate_liquidity(observation)

    assert signal.category == "Liquidity Condition"
    assert signal.score is None
    assert signal.condition == "Not scored"
    assert signal.source_status == SourceStatus.SOURCE_REQUIRED
    assert signal.used_in_final_condition is False
    assert signal.score_breakdown == []
    assert signal.missing_data == [
        "stablecoin_supply: source not connected",
        "btc_etf_flows: source not connected",
        "market_depth: source not connected",
    ]
    assert signal.evidence == [
        "DeFiLlama reported USD 65,000,000,000.00 across 2 valid chain rows.",
        "DeFi TVL is context only and is not a substitute for core liquidity observations.",
    ]


def test_evaluate_liquidity_exposes_incomplete_defi_tvl() -> None:
    observation = LiquidityObservation(
        source="DeFiLlama",
        observed_at=None,
        retrieved_at=datetime(2026, 8, 11, 18, 30, tzinfo=UTC),
        defi_tvl=MetricObservation.missing(
            "USD", "1 of 2 chain rows invalid; aggregate not computed"
        ),
        chain_count=2,
        valid_chain_count=1,
        invalid_chain_count=1,
    )

    signal = evaluate_liquidity(observation)

    assert signal.score is None
    assert signal.missing_data[-1] == (
        "defi_tvl: 1 of 2 chain rows invalid; aggregate not computed"
    )
    assert signal.evidence == [
        "DeFiLlama returned 1 valid and 1 invalid chain rows."
    ]


def test_evaluate_liquidity_scores_real_stablecoin_supply_change() -> None:
    observation = LiquidityObservation(
        source="DeFiLlama",
        observed_at=None,
        retrieved_at=datetime(2026, 8, 11, 18, 30, tzinfo=UTC),
        defi_tvl=MetricObservation.available(65_000_000_000, "USD"),
        chain_count=2,
        valid_chain_count=2,
        invalid_chain_count=0,
        stablecoin_supply=MetricObservation.available(200_000_000_000, "USD"),
        stablecoin_supply_30d_ago=MetricObservation.available(196_000_000_000, "USD"),
        stablecoin_change_30d_pct=MetricObservation.available(2.040816, "percent"),
        stablecoin_history_points=31,
    )

    signal = evaluate_liquidity(observation)

    assert signal.score == 55.1
    assert signal.is_usable() is True
    assert signal.calibration_status == CalibrationStatus.PROVISIONAL
    assert signal.data_coverage == pytest.approx(1 / 3)
    assert signal.scope == "DeFiLlama global stablecoin supply"
    assert signal.score_breakdown[0].raw_value == pytest.approx(2.040816)
