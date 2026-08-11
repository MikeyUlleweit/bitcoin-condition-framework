from datetime import UTC, datetime
from pathlib import Path

from src.models.batch import ProviderFailure
from src.models.condition import BitcoinMarketCondition
from src.models.snapshot import ResearchSnapshot
from src.pipeline.replay import replay_condition
from src.signals.condition_engine import run_condition_engine
from src.storage.research_database import ResearchDatabase
from tests.test_observation_pipeline import build_blockspace_observation


def test_database_persists_and_queries_research_snapshot(tmp_path: Path) -> None:
    cutoff = datetime(2026, 8, 11, 18, 30, tzinfo=UTC)
    observation = build_blockspace_observation()
    from src.signals.blockspace_signal import evaluate_blockspace

    signal = evaluate_blockspace(observation)
    condition = run_condition_engine(
        [signal],
        minimum_required_signals=4,
        required_categories=["Blockspace / Network Demand", "Liquidity Condition"],
    )
    snapshot = ResearchSnapshot(
        snapshot_id="snapshot-1",
        created_at=cutoff,
        information_cutoff=cutoff,
        observations=[observation],
        signals=[signal],
    )
    failure = ProviderFailure(
        provider="DeFiLlama",
        observation_type="liquidity",
        category="Liquidity Condition",
        error_type="Timeout",
        message="request timed out",
        occurred_at=cutoff,
    )
    database = ResearchDatabase(tmp_path / "research.sqlite3")

    database.initialize()
    database.record_snapshot(snapshot, condition, [failure])

    assert database.load_snapshot("snapshot-1") == snapshot
    summaries = database.list_snapshot_summaries()
    assert len(summaries) == 1
    assert summaries[0].snapshot_id == "snapshot-1"
    assert summaries[0].final_condition == BitcoinMarketCondition.NOT_ENOUGH_DATA
    assert summaries[0].observation_count == 1
    assert summaries[0].signal_count == 1
    assert summaries[0].provider_failure_count == 1
    assert database.count_rows("score_contributions") == 3
    assert database.latest_snapshot().snapshot_id == "snapshot-1"
    assert database.list_provider_failures("snapshot-1") == [failure]
    history = database.get_signal_history("Blockspace / Network Demand")
    assert len(history) == 1
    assert history[0].snapshot_id == "snapshot-1"
    assert history[0].score == signal.score
    assert replay_condition(database, "snapshot-1") == condition
