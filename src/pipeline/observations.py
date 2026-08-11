from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from src.models.batch import ObservationBatch, ProviderFailure
from src.models.category import SignalCategory
from src.models.signal import CalibrationStatus, SignalOutput, SignalType, SourceStatus
from src.models.snapshot import ResearchObservation
from src.providers.coinbase import fetch_market_regime_observation
from src.providers.coinmetrics import fetch_holder_onchain_observation
from src.providers.defillama import fetch_liquidity_observation
from src.providers.kraken import fetch_leverage_observation
from src.providers.mempool import (
    fetch_blockspace_observation,
    fetch_miner_economics_observation,
)
from src.signals.blockspace_signal import evaluate_blockspace
from src.signals.liquidity_signal import evaluate_liquidity
from src.signals.provisional import (
    evaluate_holder_onchain,
    evaluate_leverage,
    evaluate_market_regime,
    evaluate_miner_economics,
)
from src.utils.settings import get_required_categories


@dataclass(frozen=True)
class CollectorSpec:
    provider: str
    observation_type: str
    category: str
    collect: Callable[[], ResearchObservation]


def default_collectors() -> tuple[CollectorSpec, ...]:
    return (
        CollectorSpec(
            provider="mempool.space",
            observation_type="blockspace",
            category=SignalCategory.BLOCKSPACE,
            collect=fetch_blockspace_observation,
        ),
        CollectorSpec(
            provider="DeFiLlama",
            observation_type="liquidity",
            category=SignalCategory.LIQUIDITY,
            collect=fetch_liquidity_observation,
        ),
        CollectorSpec(
            provider="Coinbase Exchange",
            observation_type="market_regime",
            category=SignalCategory.MARKET_REGIME,
            collect=fetch_market_regime_observation,
        ),
        CollectorSpec(
            provider="mempool.space mining",
            observation_type="miner_economics",
            category=SignalCategory.MINER,
            collect=fetch_miner_economics_observation,
        ),
        CollectorSpec(
            provider="Kraken Futures",
            observation_type="leverage",
            category=SignalCategory.LEVERAGE,
            collect=fetch_leverage_observation,
        ),
        CollectorSpec(
            provider="Coin Metrics Community",
            observation_type="holder_onchain",
            category=SignalCategory.HOLDER,
            collect=fetch_holder_onchain_observation,
        ),
    )


def collect_live_observations(
    collectors: Sequence[CollectorSpec] | None = None,
    collected_at: datetime | None = None,
) -> ObservationBatch:
    """Collect all providers while isolating failures to their own records."""
    specs = collectors if collectors is not None else default_collectors()
    observations: list[ResearchObservation] = []
    failures: list[ProviderFailure] = []

    for spec in specs:
        try:
            observations.append(spec.collect())
        except Exception as exc:
            failure_time = collected_at or datetime.now(UTC)
            failures.append(
                ProviderFailure(
                    provider=spec.provider,
                    observation_type=spec.observation_type,
                    category=spec.category,
                    error_type=type(exc).__name__,
                    message=str(exc) or type(exc).__name__,
                    occurred_at=failure_time,
                )
            )

    return ObservationBatch(
        collected_at=collected_at or datetime.now(UTC),
        observations=observations,
        failures=failures,
    )


def _failure_signal(failure: ProviderFailure) -> SignalOutput:
    return SignalOutput(
        category=failure.category,
        score=None,
        condition="Not scored",
        signal_type=SignalType.REGIME,
        source_status=SourceStatus.DATA_UNAVAILABLE,
        used_in_final_condition=False,
        evidence=[
            f"{failure.provider} failed at {failure.occurred_at.isoformat()}.",
        ],
        risks=["Provider failure prevented a current observation."],
        required_sources=[failure.provider],
        missing_data=[
            f"{failure.provider}: {failure.error_type}: {failure.message}",
        ],
        calibration_status=CalibrationStatus.PROVISIONAL,
        data_coverage=0.0,
        scope=failure.provider,
    )


def _missing_category_signal(category: str) -> SignalOutput:
    return SignalOutput(
        category=category,
        score=None,
        condition="Not scored",
        signal_type=SignalType.REGIME,
        source_status=SourceStatus.DATA_UNAVAILABLE,
        used_in_final_condition=False,
        risks=["No collector produced an observation for this category."],
        missing_data=["No observation was collected."],
        calibration_status=CalibrationStatus.PROVISIONAL,
        data_coverage=0.0,
        scope="No current observation",
    )


def evaluate_observation_batch(batch: ObservationBatch) -> list[SignalOutput]:
    """Evaluate successes and failures into one complete category signal set."""
    signals: list[SignalOutput] = []

    evaluators: dict[str, Callable[[Any], SignalOutput]] = {
        "blockspace": evaluate_blockspace,
        "liquidity": evaluate_liquidity,
        "market_regime": evaluate_market_regime,
        "miner_economics": evaluate_miner_economics,
        "leverage": evaluate_leverage,
        "holder_onchain": evaluate_holder_onchain,
    }
    for observation in batch.observations:
        evaluator = evaluators[observation.observation_type]
        signals.append(evaluator(observation))

    signals.extend(_failure_signal(failure) for failure in batch.failures)
    existing = {signal.category for signal in signals}
    signals.extend(
        _missing_category_signal(category)
        for category in get_required_categories()
        if category not in existing
    )
    return signals
