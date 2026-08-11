from src.models.condition import ConditionResult
from src.signals.condition_engine import run_condition_engine
from src.storage.research_database import ResearchDatabase


def replay_condition(
    database: ResearchDatabase,
    snapshot_id: str,
) -> ConditionResult:
    """Replay stored signals through the current condition-engine rules."""
    snapshot = database.load_snapshot(snapshot_id)
    stored_condition = database.load_condition(snapshot_id)
    required_categories = list(
        dict.fromkeys(
            [signal.category for signal in snapshot.signals]
            + stored_condition.missing_categories
        )
    )
    return run_condition_engine(
        snapshot.signals,
        minimum_required_signals=stored_condition.minimum_required_signals,
        required_categories=required_categories,
    )
