import sqlite3
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from src.models.batch import ProviderFailure
from src.models.condition import BitcoinMarketCondition, ConditionResult
from src.models.snapshot import ResearchSnapshot


class SnapshotSummary(BaseModel):
    snapshot_id: str
    created_at: str
    information_cutoff: str
    final_condition: BitcoinMarketCondition
    usable_signal_count: int = Field(..., ge=0)
    observation_count: int = Field(..., ge=0)
    signal_count: int = Field(..., ge=0)
    provider_failure_count: int = Field(..., ge=0)


class SignalHistoryPoint(BaseModel):
    snapshot_id: str
    information_cutoff: datetime
    category: str
    score: float | None
    condition: str
    source_status: str


SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id TEXT PRIMARY KEY,
    schema_version INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    information_cutoff TEXT NOT NULL,
    final_condition TEXT NOT NULL,
    confidence_score REAL,
    usable_signal_count INTEGER NOT NULL,
    condition_json TEXT NOT NULL,
    snapshot_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS observations (
    snapshot_id TEXT NOT NULL REFERENCES snapshots(snapshot_id) ON DELETE CASCADE,
    observation_type TEXT NOT NULL,
    source TEXT NOT NULL,
    observed_at TEXT,
    retrieved_at TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, observation_type)
);

CREATE TABLE IF NOT EXISTS signals (
    snapshot_id TEXT NOT NULL REFERENCES snapshots(snapshot_id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    score REAL,
    condition TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    source_status TEXT NOT NULL,
    used_in_final_condition INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, category)
);

CREATE TABLE IF NOT EXISTS score_contributions (
    snapshot_id TEXT NOT NULL,
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    raw_value REAL NOT NULL,
    unit TEXT NOT NULL,
    normalized_score REAL NOT NULL,
    weight REAL NOT NULL,
    weighted_points REAL NOT NULL,
    rationale TEXT NOT NULL,
    FOREIGN KEY (snapshot_id, category)
        REFERENCES signals(snapshot_id, category) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS provider_failures (
    snapshot_id TEXT NOT NULL REFERENCES snapshots(snapshot_id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    observation_type TEXT NOT NULL,
    category TEXT NOT NULL,
    error_type TEXT NOT NULL,
    message TEXT NOT NULL,
    occurred_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_snapshots_cutoff
    ON snapshots(information_cutoff DESC);
CREATE INDEX IF NOT EXISTS idx_signals_category
    ON signals(category, snapshot_id);
CREATE INDEX IF NOT EXISTS idx_provider_failures_provider
    ON provider_failures(provider, occurred_at DESC);
"""


class ResearchDatabase:
    def __init__(self, path: str | Path = "data/research.sqlite3") -> None:
        self.path = Path(path)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(SCHEMA)
            connection.execute("PRAGMA user_version = 1")

    def record_snapshot(
        self,
        snapshot: ResearchSnapshot,
        condition: ConditionResult,
        failures: list[ProviderFailure],
    ) -> None:
        self.initialize()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO snapshots (
                    snapshot_id, schema_version, created_at, information_cutoff,
                    final_condition, confidence_score, usable_signal_count,
                    condition_json, snapshot_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot.snapshot_id,
                    snapshot.schema_version,
                    snapshot.created_at.isoformat(),
                    snapshot.information_cutoff.isoformat(),
                    condition.final_condition.value,
                    condition.confidence_score,
                    condition.usable_signal_count,
                    condition.model_dump_json(),
                    snapshot.model_dump_json(),
                ),
            )

            for observation in snapshot.observations:
                connection.execute(
                    """
                    INSERT INTO observations (
                        snapshot_id, observation_type, source, observed_at,
                        retrieved_at, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        snapshot.snapshot_id,
                        observation.observation_type,
                        observation.source,
                        observation.observed_at.isoformat()
                        if observation.observed_at
                        else None,
                        observation.retrieved_at.isoformat(),
                        observation.model_dump_json(),
                    ),
                )

            for signal in snapshot.signals:
                connection.execute(
                    """
                    INSERT INTO signals (
                        snapshot_id, category, score, condition, signal_type,
                        source_status, used_in_final_condition, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        snapshot.snapshot_id,
                        signal.category,
                        signal.score,
                        signal.condition,
                        signal.signal_type.value,
                        signal.source_status.value,
                        int(signal.used_in_final_condition),
                        signal.model_dump_json(),
                    ),
                )
                connection.executemany(
                    """
                    INSERT INTO score_contributions (
                        snapshot_id, category, name, raw_value, unit,
                        normalized_score, weight, weighted_points, rationale
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            snapshot.snapshot_id,
                            signal.category,
                            item.name,
                            item.raw_value,
                            item.unit,
                            item.normalized_score,
                            item.weight,
                            item.weighted_points,
                            item.rationale,
                        )
                        for item in signal.score_breakdown
                    ],
                )

            connection.executemany(
                """
                INSERT INTO provider_failures (
                    snapshot_id, provider, observation_type, category,
                    error_type, message, occurred_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        snapshot.snapshot_id,
                        failure.provider,
                        failure.observation_type,
                        failure.category,
                        failure.error_type,
                        failure.message,
                        failure.occurred_at.isoformat(),
                    )
                    for failure in failures
                ],
            )

    def load_snapshot(self, snapshot_id: str) -> ResearchSnapshot:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT snapshot_json FROM snapshots WHERE snapshot_id = ?",
                (snapshot_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Snapshot not found: {snapshot_id}")
        return ResearchSnapshot.model_validate_json(row["snapshot_json"])

    def list_snapshot_summaries(self, limit: int = 100) -> list[SnapshotSummary]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    s.snapshot_id,
                    s.created_at,
                    s.information_cutoff,
                    s.final_condition,
                    s.usable_signal_count,
                    (SELECT COUNT(*) FROM observations o
                     WHERE o.snapshot_id = s.snapshot_id) AS observation_count,
                    (SELECT COUNT(*) FROM signals g
                     WHERE g.snapshot_id = s.snapshot_id) AS signal_count,
                    (SELECT COUNT(*) FROM provider_failures f
                     WHERE f.snapshot_id = s.snapshot_id) AS provider_failure_count
                FROM snapshots s
                ORDER BY s.information_cutoff DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [SnapshotSummary.model_validate(dict(row)) for row in rows]

    def load_condition(self, snapshot_id: str) -> ConditionResult:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT condition_json FROM snapshots WHERE snapshot_id = ?",
                (snapshot_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Snapshot not found: {snapshot_id}")
        return ConditionResult.model_validate_json(row["condition_json"])

    def latest_snapshot(self) -> ResearchSnapshot:
        summaries = self.list_snapshot_summaries(limit=1)
        if not summaries:
            raise KeyError("No research snapshots are stored")
        return self.load_snapshot(summaries[0].snapshot_id)

    def list_provider_failures(self, snapshot_id: str) -> list[ProviderFailure]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT provider, observation_type, category, error_type,
                       message, occurred_at
                FROM provider_failures
                WHERE snapshot_id = ?
                ORDER BY provider
                """,
                (snapshot_id,),
            ).fetchall()
        return [ProviderFailure.model_validate(dict(row)) for row in rows]

    def get_signal_history(
        self,
        category: str,
        limit: int = 500,
    ) -> list[SignalHistoryPoint]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT g.snapshot_id, s.information_cutoff, g.category, g.score,
                       g.condition, g.source_status
                FROM signals g
                JOIN snapshots s ON s.snapshot_id = g.snapshot_id
                WHERE g.category = ?
                ORDER BY s.information_cutoff ASC
                LIMIT ?
                """,
                (category, limit),
            ).fetchall()
        return [SignalHistoryPoint.model_validate(dict(row)) for row in rows]

    def count_rows(self, table: str) -> int:
        allowed = {
            "snapshots",
            "observations",
            "signals",
            "score_contributions",
            "provider_failures",
        }
        if table not in allowed:
            raise ValueError(f"Unsupported table: {table}")
        with self._connect() as connection:
            row = connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()
        assert row is not None
        return int(row["count"])
