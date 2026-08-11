from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from src.models.blockspace import BlockspaceObservation
from src.models.observation import MetricObservation, ObservationStatus
from src.providers.mempool import fetch_blockspace_observation


class StubResponse:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self.payload


def test_blockspace_observation_represents_missing_provider_metric_explicitly() -> None:
    retrieved_at = datetime(2026, 8, 11, 18, 30, tzinfo=UTC)

    observation = BlockspaceObservation(
        source="mempool.space",
        observed_at=None,
        retrieved_at=retrieved_at,
        fastest_fee=MetricObservation.available(20, "sat/vB"),
        half_hour_fee=MetricObservation.available(15, "sat/vB"),
        hour_fee=MetricObservation.available(10, "sat/vB"),
        economy_fee=MetricObservation.missing("sat/vB", "field absent from provider payload"),
        minimum_fee=MetricObservation.available(1, "sat/vB"),
        mempool_count=MetricObservation.available(10_000, "transactions"),
        mempool_vsize=MetricObservation.available(5_000_000, "vbytes"),
        mempool_total_fee=MetricObservation.available(25_000_000, "satoshis"),
    )

    assert observation.observed_at is None
    assert observation.retrieved_at == retrieved_at
    assert observation.economy_fee.status == ObservationStatus.MISSING
    assert observation.economy_fee.value is None
    assert observation.economy_fee.missing_reason == "field absent from provider payload"


def test_available_metric_requires_a_value() -> None:
    with pytest.raises(ValidationError):
        MetricObservation(
            status=ObservationStatus.AVAILABLE,
            value=None,
            unit="sat/vB",
        )


def test_retrieval_timestamp_must_include_timezone() -> None:
    with pytest.raises(ValidationError):
        BlockspaceObservation(
            source="mempool.space",
            observed_at=None,
            retrieved_at=datetime(2026, 8, 11, 18, 30),
            fastest_fee=MetricObservation.available(20, "sat/vB"),
            half_hour_fee=MetricObservation.available(15, "sat/vB"),
            hour_fee=MetricObservation.available(10, "sat/vB"),
            economy_fee=MetricObservation.available(5, "sat/vB"),
            minimum_fee=MetricObservation.available(1, "sat/vB"),
            mempool_count=MetricObservation.available(10_000, "transactions"),
            mempool_vsize=MetricObservation.available(5_000_000, "vbytes"),
            mempool_total_fee=MetricObservation.available(25_000_000, "satoshis"),
        )


def test_fetch_blockspace_observation_validates_payloads_and_preserves_missing_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payloads = iter(
        [
            {
                "fastestFee": 20,
                "halfHourFee": 15,
                "hourFee": 10,
                "minimumFee": 1,
            },
            {
                "count": 10_000,
                "vsize": 5_000_000,
                "total_fee": 25_000_000,
            },
        ]
    )

    def fake_get(url: str, timeout: int) -> StubResponse:
        assert url.startswith("https://mempool.space/api/")
        assert timeout == 10
        return StubResponse(next(payloads))

    monkeypatch.setattr("src.providers.mempool.requests.get", fake_get)

    observation = fetch_blockspace_observation()

    assert observation.source == "mempool.space"
    assert observation.observed_at is None
    assert observation.retrieved_at.tzinfo == UTC
    assert observation.half_hour_fee == MetricObservation.available(15, "sat/vB")
    assert observation.mempool_count == MetricObservation.available(
        10_000, "transactions"
    )
    assert observation.economy_fee == MetricObservation.missing(
        "sat/vB", "economyFee absent from provider payload"
    )
