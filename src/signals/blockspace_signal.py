from src.models.blockspace import BlockspaceObservation
from src.models.category import SignalCategory
from src.models.signal import (
    CalibrationStatus,
    ScoreContribution,
    SignalOutput,
    SignalType,
    SourceStatus,
)


def _label(score: float) -> str:
    if score >= 80:
        return "Very high blockspace demand"
    if score >= 60:
        return "High blockspace demand"
    if score >= 40:
        return "Moderate blockspace demand"
    if score >= 20:
        return "Low blockspace demand"
    return "Very low blockspace demand"


def evaluate_blockspace(observation: BlockspaceObservation) -> SignalOutput:
    """Evaluate a validated blockspace observation as a standardized signal."""
    required_metrics = {
        "fastest_fee": observation.fastest_fee,
        "half_hour_fee": observation.half_hour_fee,
        "hour_fee": observation.hour_fee,
        "minimum_fee": observation.minimum_fee,
        "mempool_count": observation.mempool_count,
        "mempool_vsize": observation.mempool_vsize,
        "mempool_total_fee": observation.mempool_total_fee,
    }
    missing_data = [
        f"{name}: {metric.missing_reason}"
        for name, metric in required_metrics.items()
        if not metric.is_available
    ]
    if missing_data:
        return SignalOutput(
            category=SignalCategory.BLOCKSPACE,
            score=None,
            condition="Not scored",
            signal_type=SignalType.REGIME,
            source_status=SourceStatus.DATA_UNAVAILABLE,
            used_in_final_condition=False,
            evidence=[
                f"mempool.space payload retrieved at {observation.retrieved_at.isoformat()}."
            ],
            risks=["Blockspace demand is not scored because required observations are missing."],
            required_sources=["mempool.space"],
            missing_data=missing_data,
            input_observation_types=["blockspace"],
            calibration_status=CalibrationStatus.PROVISIONAL,
            data_coverage=(len(required_metrics) - len(missing_data)) / len(required_metrics),
            scope="Bitcoin mempool.space network snapshot",
        )

    half_hour_fee = float(observation.half_hour_fee.value or 0)
    mempool_count = float(observation.mempool_count.value or 0)
    mempool_vsize = float(observation.mempool_vsize.value or 0)
    normalized = [
        min(half_hour_fee, 100),
        min(mempool_count / 100_000 * 100, 100),
        min(mempool_vsize / 300_000_000 * 100, 100),
    ]
    weights = [0.5, 0.25, 0.25]
    contributions = [
        ScoreContribution(
            name=name,
            raw_value=raw,
            unit=unit,
            normalized_score=round(value, 2),
            weight=weight,
            weighted_points=round(value * weight, 2),
            rationale=rationale,
        )
        for name, raw, unit, value, weight, rationale in zip(
            ["Half-hour recommended fee", "Mempool transaction count", "Mempool virtual size"],
            [half_hour_fee, mempool_count, mempool_vsize],
            ["sat/vB", "transactions", "vbytes"],
            normalized,
            weights,
            [
                "Fee pressure is capped at 100 sat/vB for this version.",
                "Congestion is capped at 100,000 unconfirmed transactions.",
                "Mempool size is capped at 300,000,000 virtual bytes.",
            ],
            strict=True,
        )
    ]
    score = round(sum(item.weighted_points for item in contributions), 2)
    risks = []
    if score >= 80:
        risks.append(
            "Blockspace demand is extremely elevated, indicating congestion or fee pressure."
        )
    if half_hour_fee <= 5:
        risks.append("Fee pressure is low, which may indicate weak settlement demand.")
    return SignalOutput(
        category=SignalCategory.BLOCKSPACE,
        score=score,
        condition=_label(score),
        signal_type=SignalType.REGIME,
        source_status=SourceStatus.VALID_PUBLIC_SOURCE,
        used_in_final_condition=True,
        evidence=[
            f"Half-hour recommended fee is {half_hour_fee:g} sat/vB.",
            f"Mempool transaction count is {mempool_count:,.0f}.",
            f"Mempool vsize is {mempool_vsize:,.0f} vbytes.",
        ],
        risks=risks,
        required_sources=["mempool.space"],
        score_breakdown=contributions,
        input_observation_types=["blockspace"],
        calibration_status=CalibrationStatus.PROVISIONAL,
        data_coverage=1.0,
        scope="Bitcoin mempool.space network snapshot",
    )
