from datetime import UTC, datetime

from src.models.observation import MetricObservation
from src.models.provisional import MarketRegimeObservation, MinerEconomicsObservation
from src.models.signal import CalibrationStatus
from src.signals.provisional import evaluate_market_regime, evaluate_miner_economics


def test_market_regime_scores_btc_trend_and_fixed_universe_rotation() -> None:
    observation = MarketRegimeObservation(
        source="Coinbase Exchange",
        observed_at=datetime(2026, 8, 10, tzinfo=UTC),
        retrieved_at=datetime(2026, 8, 11, tzinfo=UTC),
        btc_return_30d_pct=MetricObservation.available(10, "percent"),
        btc_realized_volatility_30d=MetricObservation.available(45, "percent annualized"),
        eth_relative_return_30d_pct=MetricObservation.available(5, "percentage points"),
        sol_relative_return_30d_pct=MetricObservation.available(15, "percentage points"),
        product_count=3,
    )

    signal = evaluate_market_regime(observation)

    assert signal.score == 60
    assert signal.is_usable() is True
    assert signal.calibration_status == CalibrationStatus.PROVISIONAL
    assert signal.data_coverage == 1
    assert signal.scope == "Coinbase BTC-USD, ETH-USD, and SOL-USD daily candles"
    assert [item.weighted_points for item in signal.score_breakdown] == [36, 24]


def test_miner_economics_scores_public_network_and_reward_metrics() -> None:
    observation = MinerEconomicsObservation(
        source="mempool.space",
        observed_at=datetime(2026, 8, 10, tzinfo=UTC),
        retrieved_at=datetime(2026, 8, 11, tzinfo=UTC),
        hashrate_change_30d_pct=MetricObservation.available(5, "percent"),
        difficulty_adjustment_pct=MetricObservation.available(2, "percent"),
        fee_share_of_rewards_pct=MetricObservation.available(5, "percent"),
        history_points=90,
    )

    signal = evaluate_miner_economics(observation)

    assert signal.score == 57
    assert signal.is_usable() is True
    assert signal.data_coverage == 1
    assert signal.scope == "Bitcoin network miner economics from mempool.space"
