from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel

from src.models.batch import ProviderFailure
from src.models.condition import ConditionResult
from src.models.snapshot import ResearchSnapshot
from src.pipeline.observations import (
    CollectorSpec,
    collect_live_observations,
    evaluate_observation_batch,
)
from src.signals.condition_engine import run_condition_engine
from src.storage.research_database import ResearchDatabase


class LiveResearchRun(BaseModel):
    snapshot: ResearchSnapshot
    condition: ConditionResult
    provider_failures: list[ProviderFailure]


def run_live_research(
    database: ResearchDatabase,
    collectors: Sequence[CollectorSpec] | None = None,
    collected_at: datetime | None = None,
) -> LiveResearchRun:
    """Collect, evaluate, classify, snapshot, and persist one live research run."""
    batch = collect_live_observations(
        collectors=collectors,
        collected_at=collected_at,
    )
    signals = evaluate_observation_batch(batch)
    condition = run_condition_engine(signals)
    snapshot = ResearchSnapshot(
        snapshot_id=str(uuid4()),
        created_at=datetime.now(UTC),
        information_cutoff=batch.collected_at,
        observations=batch.observations,
        signals=signals,
    )
    database.record_snapshot(snapshot, condition, batch.failures)
    return LiveResearchRun(
        snapshot=snapshot,
        condition=condition,
        provider_failures=batch.failures,
    )
