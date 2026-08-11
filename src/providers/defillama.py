from datetime import UTC, datetime, timedelta

import requests

from src.models.liquidity import LiquidityObservation
from src.models.observation import MetricObservation

DEFILLAMA_BASE_URL = "https://api.llama.fi"
DEFILLAMA_STABLECOIN_URL = "https://stablecoins.llama.fi/stablecoincharts/all"


class DeFiLlamaProviderError(Exception):
    """
    Raised when the DeFiLlama provider fails.
    """


def _get_json(endpoint: str, timeout: int = 10) -> object:
    """
    Fetch JSON data from a DeFiLlama API endpoint.
    """
    url = f"{DEFILLAMA_BASE_URL}{endpoint}"

    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DeFiLlamaProviderError(f"DeFiLlama request failed: {url}") from exc

    return response.json()


def _get_stablecoin_history(timeout: int = 10) -> object:
    try:
        response = requests.get(DEFILLAMA_STABLECOIN_URL, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DeFiLlamaProviderError(
            f"DeFiLlama request failed: {DEFILLAMA_STABLECOIN_URL}"
        ) from exc
    return response.json()


def _parse_stablecoin_history(
    payload: object,
) -> tuple[MetricObservation, MetricObservation, MetricObservation, int]:
    missing_supply = MetricObservation.missing(
        "USD", "valid 30-day stablecoin history unavailable"
    )
    missing_change = MetricObservation.missing(
        "percent", "valid 30-day stablecoin history unavailable"
    )
    if not isinstance(payload, list):
        return missing_supply, missing_supply, missing_change, 0

    points: list[tuple[datetime, float]] = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        circulating = row.get("totalCirculating")
        if not isinstance(circulating, dict):
            continue
        value = circulating.get("peggedUSD")
        raw_date = row.get("date")
        if isinstance(value, bool) or not isinstance(value, int | float) or value < 0:
            continue
        try:
            timestamp = datetime.fromtimestamp(float(str(raw_date)), tz=UTC)
        except (TypeError, ValueError, OSError):
            continue
        points.append((timestamp, float(value)))

    points.sort(key=lambda item: item[0])
    if len(points) < 2:
        return missing_supply, missing_supply, missing_change, len(points)

    latest_time, latest_value = points[-1]
    cutoff = latest_time - timedelta(days=30)
    prior_points = [point for point in points if point[0] <= cutoff]
    if not prior_points or prior_points[-1][1] <= 0:
        return missing_supply, missing_supply, missing_change, len(points)

    prior_value = prior_points[-1][1]
    change_pct = (latest_value / prior_value - 1) * 100
    return (
        MetricObservation.available(latest_value, "USD"),
        MetricObservation.available(prior_value, "USD"),
        MetricObservation.available(change_pct, "percent"),
        len(points),
    )


def get_chains_tvl() -> list[dict[str, object]]:
    """
    Fetch current DeFi TVL by chain from DeFiLlama.
    """
    data = _get_json("/v2/chains")

    if not isinstance(data, list):
        raise DeFiLlamaProviderError("DeFiLlama chains response must be a list.")

    chains: list[dict[str, object]] = []

    for item in data:
        if not isinstance(item, dict):
            continue

        chains.append({str(key): value for key, value in item.items()})

    return chains


def get_total_defi_tvl() -> float:
    """
    Calculate total DeFi TVL across chains.

    This is used only as secondary liquidity context, not as a full
    institutional liquidity score.
    """
    chains = get_chains_tvl()

    total_tvl = 0.0

    for chain in chains:
        tvl = chain.get("tvl")

        if isinstance(tvl, int | float):
            total_tvl += float(tvl)

    return total_tvl


def fetch_liquidity_observation() -> LiquidityObservation:
    """Fetch DeFiLlama TVL as a validated liquidity observation."""
    payload = _get_json("/v2/chains")
    stablecoin_payload = _get_stablecoin_history()
    retrieved_at = datetime.now(UTC)

    if not isinstance(payload, list):
        raise DeFiLlamaProviderError("DeFiLlama chains response must be a list.")

    total_tvl = 0.0
    valid_chain_count = 0
    invalid_chain_count = 0
    for item in payload:
        if not isinstance(item, dict):
            invalid_chain_count += 1
            continue
        tvl = item.get("tvl")
        if isinstance(tvl, bool) or not isinstance(tvl, int | float):
            invalid_chain_count += 1
            continue
        if tvl < 0:
            invalid_chain_count += 1
            continue
        total_tvl += float(tvl)
        valid_chain_count += 1

    if invalid_chain_count:
        defi_tvl = MetricObservation.missing(
            "USD",
            f"{invalid_chain_count} of {len(payload)} chain rows invalid; "
            "aggregate not computed",
        )
    elif not payload:
        defi_tvl = MetricObservation.missing(
            "USD", "provider payload contained no chains"
        )
    else:
        defi_tvl = MetricObservation.available(total_tvl, "USD")

    stablecoin_supply, stablecoin_supply_30d_ago, stablecoin_change, history_points = (
        _parse_stablecoin_history(stablecoin_payload)
    )

    return LiquidityObservation(
        source="DeFiLlama",
        observed_at=None,
        retrieved_at=retrieved_at,
        defi_tvl=defi_tvl,
        chain_count=len(payload),
        valid_chain_count=valid_chain_count,
        invalid_chain_count=invalid_chain_count,
        stablecoin_supply=stablecoin_supply,
        stablecoin_supply_30d_ago=stablecoin_supply_30d_ago,
        stablecoin_change_30d_pct=stablecoin_change,
        stablecoin_history_points=history_points,
    )
