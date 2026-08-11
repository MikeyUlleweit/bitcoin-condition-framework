from src.models.category import SignalCategory
from src.models.provisional import (
    HolderOnChainObservation,
    LeverageObservation,
    MarketRegimeObservation,
    MinerEconomicsObservation,
)
from src.models.signal import (
    CalibrationStatus,
    ScoreContribution,
    SignalOutput,
    SignalType,
    SourceStatus,
)


def _bounded(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 2)


def evaluate_market_regime(observation: MarketRegimeObservation) -> SignalOutput:
    """Score Coinbase BTC trend and a fixed ETH/SOL rotation universe."""
    btc_return = observation.btc_return_30d_pct.value
    relative_returns = [
        metric.value
        for metric in (
            observation.eth_relative_return_30d_pct,
            observation.sol_relative_return_30d_pct,
        )
        if metric.is_available and metric.value is not None
    ]
    if btc_return is None:
        raise ValueError("BTC 30-day return is required for market regime scoring")

    trend_score = _bounded(50 + btc_return)
    rotation_score = _bounded(
        50 + sum(relative_returns) / len(relative_returns) if relative_returns else 50
    )

    score = round(trend_score * 0.6 + rotation_score * 0.4, 2)
    condition = (
        "Broad risk expansion"
        if score >= 60
        else "Defensive market regime"
        if score < 40
        else "Mixed market regime"
    )
    return SignalOutput(
        category=SignalCategory.MARKET_REGIME,
        score=score,
        condition=condition,
        signal_type=SignalType.REGIME,
        source_status=SourceStatus.VALID_PUBLIC_SOURCE,
        used_in_final_condition=True,
        evidence=[
            f"BTC returned {btc_return:.2f}% over 30 days.",
            f"{len(relative_returns)} fixed-universe alt relative return(s) were available.",
        ],
        risks=["The fixed Coinbase universe does not represent the entire crypto market."],
        required_sources=["Coinbase Exchange public candles"],
        score_breakdown=[
            ScoreContribution(
                name="BTC 30-day trend",
                raw_value=btc_return,
                unit="percent",
                normalized_score=trend_score,
                weight=0.6,
                weighted_points=round(trend_score * 0.6, 2),
                rationale="A -50% to +50% return maps linearly to 0-100.",
            ),
            ScoreContribution(
                name="ETH/SOL relative rotation",
                raw_value=sum(relative_returns) / len(relative_returns) if relative_returns else 0,
                unit="percentage points",
                normalized_score=rotation_score,
                weight=0.4,
                weighted_points=round(rotation_score * 0.4, 2),
                rationale="Average alt return relative to BTC maps around a neutral 50.",
            ),
        ],
        input_observation_types=["market_regime"],
        calibration_status=CalibrationStatus.PROVISIONAL,
        data_coverage=observation.product_count / 3,
        scope="Coinbase BTC-USD, ETH-USD, and SOL-USD daily candles",
    )


def evaluate_miner_economics(observation: MinerEconomicsObservation) -> SignalOutput:
    """Score public Bitcoin network conditions relevant to miner economics."""
    metrics = (
        observation.hashrate_change_30d_pct,
        observation.difficulty_adjustment_pct,
        observation.fee_share_of_rewards_pct,
    )
    if any(metric.value is None for metric in metrics):
        raise ValueError("all miner economics metrics are required")
    hashrate = observation.hashrate_change_30d_pct.value
    difficulty = observation.difficulty_adjustment_pct.value
    fee_share = observation.fee_share_of_rewards_pct.value
    assert hashrate is not None and difficulty is not None and fee_share is not None

    hashrate_score = _bounded(50 + hashrate * 2)
    difficulty_score = _bounded(50 + difficulty * 5)
    fee_score = _bounded(fee_share * 10)
    contributions = [
        ScoreContribution(
            name="30-day network hashrate change",
            raw_value=hashrate,
            unit="percent",
            normalized_score=hashrate_score,
            weight=0.4,
            weighted_points=round(hashrate_score * 0.4, 2),
            rationale="A -25% to +25% change maps linearly to 0-100.",
        ),
        ScoreContribution(
            name="Latest difficulty adjustment",
            raw_value=difficulty,
            unit="percent",
            normalized_score=difficulty_score,
            weight=0.3,
            weighted_points=round(difficulty_score * 0.3, 2),
            rationale="A -10% to +10% adjustment maps linearly to 0-100.",
        ),
        ScoreContribution(
            name="Transaction-fee share of miner rewards",
            raw_value=fee_share,
            unit="percent",
            normalized_score=fee_score,
            weight=0.3,
            weighted_points=round(fee_score * 0.3, 2),
            rationale="A 0% to 10% fee share maps linearly to 0-100.",
        ),
    ]
    score = round(sum(item.weighted_points for item in contributions), 2)
    condition = (
        "Supportive miner economics"
        if score >= 60
        else "Stressed miner economics"
        if score < 40
        else "Mixed miner economics"
    )
    return SignalOutput(
        category=SignalCategory.MINER,
        score=score,
        condition=condition,
        signal_type=SignalType.RISK,
        source_status=SourceStatus.VALID_PUBLIC_SOURCE,
        used_in_final_condition=True,
        evidence=[
            f"Hashrate changed {hashrate:.2f}% over 30 days.",
            f"Transaction fees were {fee_share:.2f}% of observed miner rewards.",
        ],
        risks=["This score does not include miner wallet reserves or exchange flows."],
        required_sources=["mempool.space mining API"],
        score_breakdown=contributions,
        input_observation_types=["miner_economics"],
        calibration_status=CalibrationStatus.PROVISIONAL,
        data_coverage=1.0,
        scope="Bitcoin network miner economics from mempool.space",
    )


def evaluate_leverage(observation: LeverageObservation) -> SignalOutput:
    values = [
        observation.funding_rate_30d_avg_pct.value,
        observation.open_interest_change_30d_pct.value,
        observation.futures_basis_pct.value,
    ]
    if any(value is None for value in values):
        raise ValueError("all leverage metrics are required")
    funding_value, oi_value, basis_value = values
    assert funding_value is not None and oi_value is not None and basis_value is not None
    funding, oi_change, basis = funding_value, oi_value, basis_value
    normalized = [
        _bounded(50 + abs(funding) * 1000),
        _bounded(50 + oi_change),
        _bounded(50 + abs(basis) * 10),
    ]
    weights = [0.4, 0.35, 0.25]
    names = ["30-day average funding", "30-day open-interest change", "Current futures basis"]
    raw = [funding, oi_change, basis]
    contributions = [
        ScoreContribution(
            name=n,
            raw_value=r,
            unit="percent",
            normalized_score=s,
            weight=w,
            weighted_points=round(s * w, 2),
            rationale="Public single-venue leverage-risk proxy; higher is more crowded.",
        )
        for n, r, s, w in zip(names, raw, normalized, weights, strict=True)
    ]
    score = round(sum(x.weighted_points for x in contributions), 2)
    return SignalOutput(
        category=SignalCategory.LEVERAGE,
        score=score,
        condition="Elevated leverage risk"
        if score >= 65
        else "Contained leverage risk"
        if score < 45
        else "Moderate leverage risk",
        signal_type=SignalType.RISK,
        source_status=SourceStatus.VALID_PUBLIC_SOURCE,
        used_in_final_condition=True,
        evidence=[f"Kraken PF_XBTUSD open interest changed {oi_change:.2f}% over 30 days."],
        risks=["Single-venue proxy; it excludes offshore and options positioning."],
        required_sources=["Kraken Futures public analytics"],
        score_breakdown=contributions,
        input_observation_types=["leverage"],
        calibration_status=CalibrationStatus.PROVISIONAL,
        data_coverage=1.0,
        scope="Kraken Futures PF_XBTUSD perpetual only",
    )


def evaluate_holder_onchain(observation: HolderOnChainObservation) -> SignalOutput:
    if observation.mvrv.value is None or observation.active_addresses_change_30d_pct.value is None:
        raise ValueError("MVRV and active-address change are required")
    mvrv = observation.mvrv.value
    addresses = observation.active_addresses_change_30d_pct.value
    mvrv_score = _bounded(100 - abs(mvrv - 1.5) * 50)
    address_score = _bounded(50 + addresses * 2)
    contributions = [
        ScoreContribution(
            name="Current MVRV",
            raw_value=mvrv,
            unit="ratio",
            normalized_score=mvrv_score,
            weight=0.7,
            weighted_points=round(mvrv_score * 0.7, 2),
            rationale="Distance from a provisional 1.5 neutral anchor reduces the score.",
        ),
        ScoreContribution(
            name="30-day active-address change",
            raw_value=addresses,
            unit="percent",
            normalized_score=address_score,
            weight=0.3,
            weighted_points=round(address_score * 0.3, 2),
            rationale="A -25% to +25% change maps linearly to 0-100.",
        ),
    ]
    score = round(sum(x.weighted_points for x in contributions), 2)
    return SignalOutput(
        category=SignalCategory.HOLDER,
        score=score,
        condition="Supportive on-chain condition"
        if score >= 60
        else "Weak on-chain condition"
        if score < 40
        else "Mixed on-chain condition",
        signal_type=SignalType.RISK,
        source_status=SourceStatus.VALID_PUBLIC_SOURCE,
        used_in_final_condition=True,
        evidence=[f"Coin Metrics MVRV was {mvrv:.2f}."],
        risks=["Community metrics are broad proxies, not holder-cohort realized-cap analysis."],
        required_sources=["Coin Metrics Community API"],
        score_breakdown=contributions,
        input_observation_types=["holder_onchain"],
        calibration_status=CalibrationStatus.PROVISIONAL,
        data_coverage=1.0,
        scope="Bitcoin MVRV and active addresses from Coin Metrics Community",
    )
