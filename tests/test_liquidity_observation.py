from datetime import UTC, datetime

import pytest

from src.models.observation import MetricObservation
from src.providers.defillama import fetch_liquidity_observation


class StubResponse:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self.payload


def test_fetch_liquidity_observation_returns_validated_defi_tvl(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, timeout: int) -> StubResponse:
        assert timeout == 10
        if url == "https://api.llama.fi/v2/chains":
            return StubResponse(
                [
                    {"name": "Ethereum", "tvl": 60_000_000_000},
                    {"name": "Bitcoin", "tvl": 5_000_000_000},
                ]
            )
        assert url == "https://stablecoins.llama.fi/stablecoincharts/all"
        return StubResponse(
            [
                {
                    "date": str(int(datetime(2026, 7, 12, tzinfo=UTC).timestamp())),
                    "totalCirculating": {"peggedUSD": 196_000_000_000},
                },
                {
                    "date": str(int(datetime(2026, 8, 11, tzinfo=UTC).timestamp())),
                    "totalCirculating": {"peggedUSD": 200_000_000_000},
                },
            ]
        )

    monkeypatch.setattr("src.providers.defillama.requests.get", fake_get)

    observation = fetch_liquidity_observation()

    assert observation.source == "DeFiLlama"
    assert observation.observed_at is None
    assert observation.retrieved_at.tzinfo == UTC
    assert observation.chain_count == 2
    assert observation.valid_chain_count == 2
    assert observation.invalid_chain_count == 0
    assert observation.defi_tvl == MetricObservation.available(65_000_000_000, "USD")
    assert observation.stablecoin_supply == MetricObservation.available(
        200_000_000_000, "USD"
    )
    assert observation.stablecoin_change_30d_pct.value == pytest.approx(2.040816)


def test_fetch_liquidity_observation_never_sums_partial_chain_coverage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, timeout: int) -> StubResponse:
        if url == "https://stablecoins.llama.fi/stablecoincharts/all":
            return StubResponse([])
        return StubResponse(
            [
                {"name": "Ethereum", "tvl": 60_000_000_000},
                {"name": "Malformed chain without TVL"},
            ]
        )

    monkeypatch.setattr("src.providers.defillama.requests.get", fake_get)

    observation = fetch_liquidity_observation()

    assert observation.chain_count == 2
    assert observation.valid_chain_count == 1
    assert observation.invalid_chain_count == 1
    assert observation.defi_tvl == MetricObservation.missing(
        "USD", "1 of 2 chain rows invalid; aggregate not computed"
    )
