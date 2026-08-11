from src.models.condition import BitcoinMarketCondition, ConditionResult
from src.models.signal import SignalOutput, SignalType, SourceStatus
from src.signals.condition_engine import (
    get_missing_categories,
    get_usable_signals,
    run_condition_engine,
)


def make_signal(
    category: str,
    score: float | None,
    source_status: SourceStatus,
    used_in_final_condition: bool,
) -> SignalOutput:
    return SignalOutput(
        category=category,
        score=score,
        condition="Test condition",
        signal_type=SignalType.REGIME,
        source_status=source_status,
        used_in_final_condition=used_in_final_condition,
        evidence=["Test evidence."],
        risks=[],
        required_sources=["Test source"],
    )


def test_condition_result_not_enough_data_is_not_classified():
    result = ConditionResult(
        final_condition=BitcoinMarketCondition.NOT_ENOUGH_DATA,
        confidence_score=None,
        usable_signal_count=1,
        minimum_required_signals=4,
        usable_signals=[],
        missing_categories=[
            "Liquidity Condition",
            "Miner Condition",
            "Holder Condition",
        ],
        summary="Not enough connected data to classify the Bitcoin market condition.",
        evidence=[],
        risks=["Only one usable signal is connected."],
    )

    assert result.is_classified() is False


def test_condition_result_expansion_is_classified():
    signal = make_signal(
        category="Liquidity Condition",
        score=72,
        source_status=SourceStatus.CONNECTED,
        used_in_final_condition=True,
    )

    result = ConditionResult(
        final_condition=BitcoinMarketCondition.EXPANSION,
        confidence_score=70,
        usable_signal_count=4,
        minimum_required_signals=4,
        usable_signals=[signal],
        missing_categories=[],
        summary="Bitcoin conditions are broadly supportive.",
        evidence=["Liquidity is supportive."],
        risks=["Leverage should still be monitored."],
    )

    assert result.is_classified() is True


def test_get_usable_signals_only_returns_valid_connected_signals():
    signals = [
        make_signal("Liquidity Condition", 70, SourceStatus.CONNECTED, True),
        make_signal("Holder Condition", None, SourceStatus.SOURCE_REQUIRED, False),
        make_signal("Leverage Condition", 55, SourceStatus.NOT_SCORED, True),
        make_signal("Blockspace / Network Demand", 62, SourceStatus.VALID_PUBLIC_SOURCE, True),
    ]

    usable = get_usable_signals(signals)

    assert len(usable) == 2
    assert usable[0].category == "Liquidity Condition"
    assert usable[1].category == "Blockspace / Network Demand"


def test_get_missing_categories():
    usable_signals = [
        make_signal("Liquidity Condition", 70, SourceStatus.CONNECTED, True),
        make_signal("Blockspace / Network Demand", 62, SourceStatus.VALID_PUBLIC_SOURCE, True),
    ]

    missing = get_missing_categories(
        usable_signals=usable_signals,
        required_categories=[
            "Liquidity Condition",
            "Holder Condition",
            "Blockspace / Network Demand",
        ],
    )

    assert missing == ["Holder Condition"]


def test_run_condition_engine_returns_not_enough_data_when_too_few_signals():
    signals = [
        make_signal("Blockspace / Network Demand", 62, SourceStatus.VALID_PUBLIC_SOURCE, True),
    ]

    result = run_condition_engine(signals, minimum_required_signals=4)

    assert result.final_condition == BitcoinMarketCondition.NOT_ENOUGH_DATA
    assert result.is_classified() is False
    assert result.usable_signal_count == 1
    assert "Liquidity Condition" in result.missing_categories


def test_run_condition_engine_returns_neutral_mixed_when_enough_signals_but_no_classifier_yet():
    signals = [
        make_signal("Liquidity Condition", 70, SourceStatus.CONNECTED, True),
        make_signal("Miner Condition", 55, SourceStatus.CONNECTED, True),
        make_signal("Holder Condition", 60, SourceStatus.CONNECTED, True),
        make_signal("Leverage Condition", 50, SourceStatus.CONNECTED, True),
    ]

    result = run_condition_engine(signals, minimum_required_signals=4)

    assert result.final_condition == BitcoinMarketCondition.NEUTRAL_MIXED
    assert result.is_classified() is True
    assert result.usable_signal_count == 4