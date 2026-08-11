from datetime import UTC, datetime

from src.models.blockspace import BlockspaceObservation
from src.models.observation import MetricObservation
from src.models.signal import CalibrationStatus
from src.signals.blockspace_signal import evaluate_blockspace


def test_evaluate_blockspace_returns_explainable_standard_signal() -> None:
    observation = BlockspaceObservation(
        source="mempool.space",
        observed_at=None,
        retrieved_at=datetime(2026, 8, 11, 18, 30, tzinfo=UTC),
        fastest_fee=MetricObservation.available(20, "sat/vB"),
        half_hour_fee=MetricObservation.available(15, "sat/vB"),
        hour_fee=MetricObservation.available(10, "sat/vB"),
        economy_fee=MetricObservation.available(5, "sat/vB"),
        minimum_fee=MetricObservation.available(1, "sat/vB"),
        mempool_count=MetricObservation.available(10_000, "transactions"),
        mempool_vsize=MetricObservation.available(5_000_000, "vbytes"),
        mempool_total_fee=MetricObservation.available(25_000_000, "satoshis"),
    )

    signal = evaluate_blockspace(observation)

    assert signal.category == "Blockspace / Network Demand"
    assert signal.score == 10.42
    assert signal.calibration_status == CalibrationStatus.PROVISIONAL
    assert signal.data_coverage == 1.0
    assert signal.scope == "Bitcoin mempool.space network snapshot"
    assert signal.missing_data == []
    assert [item.name for item in signal.score_breakdown] == [
        "Half-hour recommended fee",
        "Mempool transaction count",
        "Mempool virtual size",
    ]
    assert [item.weight for item in signal.score_breakdown] == [0.5, 0.25, 0.25]
    assert [item.weighted_points for item in signal.score_breakdown] == [7.5, 2.5, 0.42]
    assert sum(item.weighted_points for item in signal.score_breakdown) == signal.score


def test_evaluate_blockspace_does_not_score_missing_core_observation() -> None:
    observation = BlockspaceObservation(
        source="mempool.space",
        observed_at=None,
        retrieved_at=datetime(2026, 8, 11, 18, 30, tzinfo=UTC),
        fastest_fee=MetricObservation.available(20, "sat/vB"),
        half_hour_fee=MetricObservation.missing(
            "sat/vB", "halfHourFee absent from provider payload"
        ),
        hour_fee=MetricObservation.available(10, "sat/vB"),
        economy_fee=MetricObservation.available(5, "sat/vB"),
        minimum_fee=MetricObservation.available(1, "sat/vB"),
        mempool_count=MetricObservation.available(10_000, "transactions"),
        mempool_vsize=MetricObservation.available(5_000_000, "vbytes"),
        mempool_total_fee=MetricObservation.available(25_000_000, "satoshis"),
    )

    signal = evaluate_blockspace(observation)

    assert signal.score is None
    assert signal.used_in_final_condition is False
    assert signal.condition == "Not scored"
    assert signal.score_breakdown == []
    assert signal.missing_data == [
        "half_hour_fee: halfHourFee absent from provider payload"
    ]
