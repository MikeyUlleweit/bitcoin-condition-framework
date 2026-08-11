from datetime import UTC, datetime
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.models.blockspace import BlockspaceObservation
from src.models.observation import MetricObservation
from src.pipeline.live_research import run_live_research
from src.pipeline.observations import CollectorSpec
from src.storage.research_database import ResearchDatabase

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def build_observation() -> BlockspaceObservation:
    return BlockspaceObservation(
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


def test_dashboard_starts_with_empty_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BITCOIN_RESEARCH_DB", str(tmp_path / "research.sqlite3"))

    app = AppTest.from_file(APP_PATH).run(timeout=20)

    assert app.exception == []
    assert app.title[0].value == "Bitcoin Market Condition Research"
    assert any("contains no snapshots" in message.value for message in app.info)


def test_dashboard_renders_persisted_research_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "populated.sqlite3"
    database = ResearchDatabase(database_path)
    observation = build_observation()

    def fail_liquidity() -> BlockspaceObservation:
        raise RuntimeError("rate limited")

    run_live_research(
        database,
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
    monkeypatch.setenv("BITCOIN_RESEARCH_DB", str(database_path))

    app = AppTest.from_file(APP_PATH).run(timeout=20)

    assert app.exception == []
    assert any(metric.label == "Market condition" for metric in app.metric)
    assert any("providers failed" in message.value.lower() for message in app.error)
