from src.models.condition import BitcoinMarketCondition, ConditionResult
from src.models.signal import SignalOutput
from src.utils.settings import get_minimum_required_signals, get_required_categories


def get_usable_signals(signals: list[SignalOutput]) -> list[SignalOutput]:
    """
    Return only signals that are eligible for the final condition engine.
    """
    return [signal for signal in signals if signal.is_usable()]


def get_not_scored_signals(signals: list[SignalOutput]) -> list[SignalOutput]:
    """
    Return signals that were built but are not eligible for scoring.
    """
    return [signal for signal in signals if not signal.is_usable()]


def get_missing_categories(
    usable_signals: list[SignalOutput],
    required_categories: list[str] | None = None,
) -> list[str]:
    """
    Return required categories that are not represented by usable signals.
    """
    if required_categories is None:
        required_categories = get_required_categories()

    usable_categories = {signal.category for signal in usable_signals}

    return [
        category
        for category in required_categories
        if category not in usable_categories
    ]


def run_condition_engine(
    signals: list[SignalOutput],
    minimum_required_signals: int | None = None,
    required_categories: list[str] | None = None,
) -> ConditionResult:
    """
    Run the Bitcoin condition engine.

    The first version determines whether the framework has enough
    connected data to produce a final condition.
    """
    if minimum_required_signals is None:
        minimum_required_signals = get_minimum_required_signals()

    if required_categories is None:
        required_categories = get_required_categories()

    usable_signals = get_usable_signals(signals)
    not_scored_signals = get_not_scored_signals(signals)
    missing_categories = get_missing_categories(
        usable_signals=usable_signals,
        required_categories=required_categories,
    )

    if len(usable_signals) < minimum_required_signals:
        return ConditionResult(
            final_condition=BitcoinMarketCondition.NOT_ENOUGH_DATA,
            confidence_score=None,
            usable_signal_count=len(usable_signals),
            minimum_required_signals=minimum_required_signals,
            usable_signals=usable_signals,
            not_scored_signals=not_scored_signals,
            missing_categories=missing_categories,
            summary=(
                "Not enough connected data to classify the "
                "Bitcoin market condition."
            ),
            evidence=[
                f"{len(usable_signals)} usable signal(s) connected.",
                f"{len(not_scored_signals)} signal(s) built but not scored.",
            ],
            risks=[
                (
                    "The framework should not produce a full market condition "
                    "until enough real signals are connected."
                ),
                "Missing or unconnected categories are excluded from scoring.",
            ],
        )

    supportive_scores = [
        100 - signal.score if signal.category == "Leverage Condition" else signal.score
        for signal in usable_signals
        if signal.score is not None
    ]
    composite = sum(supportive_scores) / len(supportive_scores)
    leverage = next(
        (signal.score for signal in usable_signals if signal.category == "Leverage Condition"),
        None,
    )
    if composite >= 60 and leverage is not None and leverage >= 70:
        final_condition = BitcoinMarketCondition.OVERHEATED
    elif composite >= 70:
        final_condition = BitcoinMarketCondition.EXPANSION
    elif composite >= 60:
        final_condition = BitcoinMarketCondition.ACCUMULATION
    elif composite >= 40:
        final_condition = BitcoinMarketCondition.NEUTRAL_MIXED
    elif composite >= 25:
        final_condition = BitcoinMarketCondition.DISTRIBUTION
    else:
        final_condition = BitcoinMarketCondition.STRESS_CAPITULATION
    confidence = round(
        sum(signal.data_coverage for signal in usable_signals) / len(usable_signals) * 100,
        2,
    )

    return ConditionResult(
        final_condition=final_condition,
        confidence_score=confidence,
        usable_signal_count=len(usable_signals),
        minimum_required_signals=minimum_required_signals,
        usable_signals=usable_signals,
        not_scored_signals=not_scored_signals,
        missing_categories=missing_categories,
        summary=(
            f"Provisional public-data composite is {composite:.2f}/100; "
            "leverage is inverted because its score measures risk intensity."
        ),
        evidence=[
            f"{len(usable_signals)} usable signal(s) connected.",
            f"{len(not_scored_signals)} signal(s) built but not scored.",
            f"Coverage-weight confidence is {confidence:.2f}%.",
        ],
        risks=[
            "Thresholds and weights are provisional and not yet backtested.",
        ],
    )
