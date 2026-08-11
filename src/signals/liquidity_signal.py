from src.models.category import SignalCategory
from src.models.liquidity import LiquidityObservation
from src.models.signal import (
    CalibrationStatus,
    ScoreContribution,
    SignalOutput,
    SignalType,
    SourceStatus,
)


def _label(score: float) -> str:
    if score >= 80:
        return "Very supportive liquidity"
    if score >= 60:
        return "Supportive liquidity"
    if score >= 40:
        return "Neutral liquidity"
    if score >= 20:
        return "Weak liquidity"
    return "Very weak liquidity"


def evaluate_liquidity(observation: LiquidityObservation) -> SignalOutput:
    """Evaluate stablecoin supply when available, preserving TVL as context only."""
    stablecoin_change = observation.stablecoin_change_30d_pct
    if stablecoin_change.is_available and stablecoin_change.value is not None:
        score = round(max(0.0, min(100.0, 50 + stablecoin_change.value * 2.5)), 2)
        return SignalOutput(
            category=SignalCategory.LIQUIDITY,
            score=score,
            condition=_label(score),
            signal_type=SignalType.REGIME,
            source_status=SourceStatus.VALID_PUBLIC_SOURCE,
            used_in_final_condition=True,
            evidence=[
                f"Global stablecoin supply changed {stablecoin_change.value:.2f}% over 30 days.",
                f"Stablecoin history contains {observation.stablecoin_history_points} points.",
            ],
            risks=[
                "ETF flows and institutional market depth are not included "
                "in this provisional score."
            ],
            required_sources=[
                "DeFiLlama stablecoin history",
                "ETF flow source",
                "Institutional market-depth source",
            ],
            score_breakdown=[
                ScoreContribution(
                    name="30-day stablecoin supply change",
                    raw_value=stablecoin_change.value,
                    unit="percent",
                    normalized_score=score,
                    weight=1.0,
                    weighted_points=score,
                    rationale="A -20% to +20% change maps linearly to 0-100.",
                )
            ],
            missing_data=[
                "btc_etf_flows: source not connected",
                "market_depth: source not connected",
            ],
            input_observation_types=["liquidity"],
            calibration_status=CalibrationStatus.PROVISIONAL,
            data_coverage=1 / 3,
            scope="DeFiLlama global stablecoin supply",
        )

    tvl_available = observation.defi_tvl.is_available and observation.defi_tvl.value is not None
    missing_data = [
        "stablecoin_supply: source not connected",
        "btc_etf_flows: source not connected",
        "market_depth: source not connected",
    ]
    if not tvl_available:
        missing_data.append(f"defi_tvl: {observation.defi_tvl.missing_reason}")
    evidence = (
        [
            f"{observation.source} reported USD {observation.defi_tvl.value:,.2f} "
            f"across {observation.valid_chain_count} valid chain rows.",
            "DeFi TVL is context only and is not a substitute for core liquidity observations.",
        ]
        if tvl_available
        else [
            f"{observation.source} returned {observation.valid_chain_count} valid and "
            f"{observation.invalid_chain_count} invalid chain rows."
        ]
    )
    return SignalOutput(
        category=SignalCategory.LIQUIDITY,
        score=None,
        condition="Not scored",
        signal_type=SignalType.REGIME,
        source_status=SourceStatus.SOURCE_REQUIRED,
        used_in_final_condition=False,
        evidence=evidence,
        risks=["Liquidity Condition is not scored because required core components are missing."],
        required_sources=["DeFiLlama stablecoin history", "ETF flow source", "Market-depth source"],
        missing_data=missing_data,
        input_observation_types=["liquidity"],
        calibration_status=CalibrationStatus.PROVISIONAL,
        data_coverage=0.0,
        scope="DeFiLlama TVL context only",
    )
