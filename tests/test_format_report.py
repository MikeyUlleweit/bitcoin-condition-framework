from src.models.condition import BitcoinMarketCondition, ConditionResult
from src.models.signal import SignalOutput, SignalType, SourceStatus
from src.reports.format_report import format_condition_report


def test_format_condition_report():
    signal = SignalOutput(
        category="Blockspace / Network Demand",
        score=26.37,
        condition="Low blockspace demand",
        signal_type=SignalType.REGIME,
        source_status=SourceStatus.VALID_PUBLIC_SOURCE,
        used_in_final_condition=True,
        evidence=["Half-hour fee is 1 sat/vB."],
        risks=["Fee pressure is low."],
        required_sources=["mempool.space"],
    )

    result = ConditionResult(
        final_condition=BitcoinMarketCondition.NOT_ENOUGH_DATA,
        confidence_score=None,
        usable_signal_count=1,
        minimum_required_signals=4,
        usable_signals=[signal],
        missing_categories=["Liquidity Condition", "Holder Condition"],
        summary="Not enough connected data to classify the Bitcoin market condition.",
        evidence=["1 usable signal(s) connected."],
        risks=["Missing or unconnected categories are excluded from scoring."],
    )

    report = format_condition_report(result)

    assert "Bitcoin Market Condition Report" in report
    assert "Final Condition: Not enough connected data" in report
    assert "Confidence Score: Not scored" in report
    assert "Blockspace / Network Demand" in report
    assert "Liquidity Condition" in report