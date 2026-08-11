from datetime import UTC, datetime
from pathlib import Path

from src.models.blockspace import BlockspaceObservation
from src.models.observation import MetricObservation
from src.models.signal import SourceStatus
from src.pipeline.live_research import run_live_research
from src.pipeline.observations import (
    CollectorSpec,
    collect_live_observations,
    evaluate_observation_batch,
)
from src.storage.research_database import ResearchDatabase


def build_blockspace_observation() -> BlockspaceObservation:
    retrieved_at = datetime(2026, 8, 11, 18, 30, tzinfo=UTC)
    return BlockspaceObservation(
        source="mempool.space",
        observed_at=None,
        retrieved_at=retrieved_at,
        fastest_fee=MetricObservation.available(20, "sat/vB"),
        half_hour_fee=MetricObservation.available(15, "sat/vB"),
        hour_fee=MetricObservation.available(10, "sat/vB"),
        economy_fee=MetricObservation.available(5, "sat/vB"),
        minimum_fee=MetricObservation.available(1, "sat/vB"),
        mempool_count=MetricObservation.available(10_000, "transactions"),
        mempool_vsize=MetricObservation.available(5_000_000, "vbytes"),
        mempool_total_fee=MetricObservation.available(25_000_000, "satoshis"),
    )


def test_collection_isolates_provider_failure() -> None:
    observation = build_blockspace_observation()

    def fail_liquidity() -> BlockspaceObservation:
        raise RuntimeError("rate limited")

    batch = collect_live_observations(
        collectors=[
            CollectorSpec(
                provider="mempool.space",
                observation_type="blockspace",
                category="Blockspace / Network Demand",
                collect=lambda: observation,
            ),
            CollectorSpec(
                provider="DeFiLlama",
                observation_type="liquidity",
                category="Liquidity Condition",
                collect=fail_liquidity,
            ),
        ],
        collected_at=datetime(2026, 8, 11, 18, 31, tzinfo=UTC),
    )

    assert batch.observations == [observation]
    assert len(batch.failures) == 1
    assert batch.failures[0].provider == "DeFiLlama"
    assert batch.failures[0].observation_type == "liquidity"
    assert batch.failures[0].message == "rate limited"

    signals = evaluate_observation_batch(batch)
    signals_by_category = {signal.category: signal for signal in signals}

    assert len(signals_by_category) == 6
    assert signals_by_category["Blockspace / Network Demand"].is_usable() is True
    assert signals_by_category["Liquidity Condition"].source_status == (
        SourceStatus.DATA_UNAVAILABLE
    )
    assert signals_by_category["Liquidity Condition"].missing_data == [
        "DeFiLlama: RuntimeError: rate limited"
    ]


def test_live_research_run_persists_complete_category_set(tmp_path: Path) -> None:
    observation = build_blockspace_observation()
    database = ResearchDatabase(tmp_path / "research.sqlite3")
    cutoff = datetime(2026, 8, 11, 18, 31, tzinfo=UTC)

    def fail_liquidity() -> BlockspaceObservation:
        raise RuntimeError("rate limited")

    run = run_live_research(
        database=database,
        collectors=[
            CollectorSpec(
                provider="mempool.space",
                observation_type="blockspace",
                category="Blockspace / Network Demand",
                collect=lambda: observation,
            ),
            CollectorSpec(
                provider="DeFiLlama",
                observation_type="liquidity",
                category="Liquidity Condition",
                collect=fail_liquidity,
            ),
        ],
        collected_at=cutoff,
    )

    assert len(run.snapshot.signals) == 6
    assert run.snapshot.information_cutoff == cutoff
    assert database.load_snapshot(run.snapshot.snapshot_id) == run.snapshot
    assert database.load_condition(run.snapshot.snapshot_id) == run.condition
