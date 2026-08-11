from datetime import UTC, datetime
from typing import Any

import requests

from src.models.blockspace import BlockspaceObservation
from src.models.observation import MetricObservation
from src.models.provisional import MinerEconomicsObservation

MEMPOOL_BASE_URL = "https://mempool.space/api"


class MempoolProviderError(Exception):
    """
    Raised when the mempool.space provider fails.
    """


def _get_json(endpoint: str, timeout: int = 10) -> Any:
    """
    Fetch JSON data from a mempool.space API endpoint.
    """
    url = f"{MEMPOOL_BASE_URL}{endpoint}"

    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise MempoolProviderError(f"mempool.space request failed: {url}") from exc

    return response.json()


def get_recommended_fees() -> dict[str, int]:
    """
    Get recommended Bitcoin transaction fees from mempool.space.

    Expected fields usually include:
    - fastestFee
    - halfHourFee
    - hourFee
    - economyFee
    - minimumFee
    """
    data = _get_json("/v1/fees/recommended")

    if not isinstance(data, dict):
        raise MempoolProviderError("Recommended fees response must be a dictionary.")

    return {str(key): int(value) for key, value in data.items()}


def get_mempool_summary() -> dict[str, int | float]:
    """
    Get current mempool summary from mempool.space.

    Expected fields usually include:
    - count
    - vsize
    - total_fee
    - fee_histogram
    """
    data = _get_json("/mempool")

    if not isinstance(data, dict):
        raise MempoolProviderError("Mempool summary response must be a dictionary.")

    summary: dict[str, int | float] = {}

    for key, value in data.items():
        if key == "fee_histogram":
            continue

        if isinstance(value, int | float):
            summary[str(key)] = value

    return summary


def _read_metric(
    payload: dict[str, object],
    field: str,
    unit: str,
) -> MetricObservation:
    if field not in payload:
        return MetricObservation.missing(unit, f"{field} absent from provider payload")

    value = payload[field]
    if isinstance(value, bool) or not isinstance(value, int | float):
        return MetricObservation.missing(unit, f"{field} is not numeric")
    if value < 0:
        return MetricObservation.missing(unit, f"{field} is negative")

    return MetricObservation.available(value, unit)


def fetch_blockspace_observation() -> BlockspaceObservation:
    """Fetch and validate the current mempool.space blockspace observation."""
    fees_payload = _get_json("/v1/fees/recommended")
    mempool_payload = _get_json("/mempool")

    if not isinstance(fees_payload, dict):
        raise MempoolProviderError("Recommended fees response must be a dictionary.")
    if not isinstance(mempool_payload, dict):
        raise MempoolProviderError("Mempool summary response must be a dictionary.")

    fees = {str(key): value for key, value in fees_payload.items()}
    mempool = {str(key): value for key, value in mempool_payload.items()}

    return BlockspaceObservation(
        source="mempool.space",
        observed_at=None,
        retrieved_at=datetime.now(UTC),
        fastest_fee=_read_metric(fees, "fastestFee", "sat/vB"),
        half_hour_fee=_read_metric(fees, "halfHourFee", "sat/vB"),
        hour_fee=_read_metric(fees, "hourFee", "sat/vB"),
        economy_fee=_read_metric(fees, "economyFee", "sat/vB"),
        minimum_fee=_read_metric(fees, "minimumFee", "sat/vB"),
        mempool_count=_read_metric(mempool, "count", "transactions"),
        mempool_vsize=_read_metric(mempool, "vsize", "vbytes"),
        mempool_total_fee=_read_metric(mempool, "total_fee", "satoshis"),
    )


def _subsidy_sats(height: int) -> int:
    return int(5_000_000_000 // (2 ** (height // 210_000)))


def fetch_miner_economics_observation() -> MinerEconomicsObservation:
    """Fetch public network history relevant to miner economics."""
    hashrate = _get_json("/v1/mining/hashrate/3m")
    rewards = _get_json("/v1/mining/blocks/rewards/3m")
    if not isinstance(hashrate, dict) or not isinstance(rewards, list):
        raise MempoolProviderError("Invalid mining payload.")
    points = sorted(
        (int(row["timestamp"]), float(row["avgHashrate"]))
        for row in hashrate.get("hashrates", [])
        if isinstance(row, dict) and float(row.get("avgHashrate", 0)) > 0
    )
    difficulties = hashrate.get("difficulty", [])
    reward_rows = [row for row in rewards if isinstance(row, dict)]
    if len(points) < 2 or not isinstance(difficulties, list) or not difficulties or not reward_rows:
        raise MempoolProviderError("Incomplete mining history.")
    cutoff = points[-1][0] - 30 * 86400
    prior = min(points, key=lambda point: abs(point[0] - cutoff))
    hash_change = (points[-1][1] / prior[1] - 1) * 100
    latest_diff = sorted(difficulties, key=lambda row: row["time"])[-1]
    difficulty_pct = (float(latest_diff["adjustment"]) - 1) * 100
    latest_reward = sorted(reward_rows, key=lambda row: row["timestamp"])[-1]
    reward_sats = float(latest_reward["avgRewards"])
    subsidy = _subsidy_sats(int(latest_reward["avgHeight"]))
    if reward_sats <= 0:
        raise MempoolProviderError("Invalid miner reward value.")
    fee_share = max(0.0, (reward_sats - subsidy) / reward_sats * 100)
    return MinerEconomicsObservation(
        source="mempool.space",
        observed_at=datetime.fromtimestamp(points[-1][0], tz=UTC),
        retrieved_at=datetime.now(UTC),
        hashrate_change_30d_pct=MetricObservation.available(hash_change, "percent"),
        difficulty_adjustment_pct=MetricObservation.available(difficulty_pct, "percent"),
        fee_share_of_rewards_pct=MetricObservation.available(fee_share, "percent"),
        history_points=len(points),
    )
