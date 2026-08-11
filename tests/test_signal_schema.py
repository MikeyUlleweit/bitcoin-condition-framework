import pytest
from pydantic import ValidationError

from src.models.signal import SignalOutput, SignalType, SourceStatus


def test_connected_signal_is_usable():
    signal = SignalOutput(
        category="Blockspace / Network Demand",
        score=62,
        condition="Moderate blockspace demand",
        signal_type=SignalType.REGIME,
        source_status=SourceStatus.VALID_PUBLIC_SOURCE,
        used_in_final_condition=True,
        evidence=["Recommended fees are elevated."],
        risks=["Fee revenue share requires richer validation."],
        required_sources=["mempool.space"],
    )

    assert signal.is_usable() is True


def test_source_required_signal_is_not_usable():
    signal = SignalOutput(
        category="Holder Condition",
        score=None,
        condition="Not scored",
        signal_type=SignalType.REGIME,
        source_status=SourceStatus.SOURCE_REQUIRED,
        used_in_final_condition=False,
        evidence=[],
        risks=["LTH supply is not connected."],
        required_sources=["Glassnode", "Coin Metrics", "CryptoQuant"],
    )

    assert signal.is_usable() is False


def test_score_must_be_between_0_and_100():
    with pytest.raises(ValidationError):
        SignalOutput(
            category="Leverage Condition",
            score=150,
            condition="Invalid score",
            signal_type=SignalType.RISK,
            source_status=SourceStatus.CONNECTED,
            used_in_final_condition=True,
        )


def test_category_cannot_be_empty():
    with pytest.raises(ValidationError):
        SignalOutput(
            category="",
            score=50,
            condition="Neutral",
            signal_type=SignalType.REGIME,
            source_status=SourceStatus.CONNECTED,
            used_in_final_condition=True,
        )