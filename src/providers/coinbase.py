from datetime import UTC, datetime
from math import log, sqrt
from statistics import stdev

from src.models.observation import MetricObservation
from src.models.provisional import MarketRegimeObservation
from src.providers.http import PublicProviderError, get_json


def _returns(product: str) -> tuple[float, float, datetime]:
    payload = get_json(
        f"https://api.exchange.coinbase.com/products/{product}/candles",
        {"granularity": 86400},
    )
    if not isinstance(payload, list):
        raise PublicProviderError(f"invalid Coinbase candles for {product}")
    points: list[tuple[int, float]] = []
    for row in payload:
        if isinstance(row, list) and len(row) >= 6:
            try:
                epoch, close = int(row[0]), float(row[4])
            except (TypeError, ValueError):
                continue
            if close > 0:
                points.append((epoch, close))
    points = sorted(set(points))
    if len(points) < 31:
        raise PublicProviderError(f"fewer than 31 valid Coinbase candles for {product}")
    window = points[-31:]
    daily = [log(window[i][1] / window[i - 1][1]) for i in range(1, len(window))]
    return_pct = (window[-1][1] / window[0][1] - 1) * 100
    volatility = stdev(daily) * sqrt(365) * 100
    return return_pct, volatility, datetime.fromtimestamp(window[-1][0], tz=UTC)


def fetch_market_regime_observation() -> MarketRegimeObservation:
    retrieved = datetime.now(UTC)
    values: dict[str, tuple[float, float, datetime]] = {}
    for product in ("BTC-USD", "ETH-USD", "SOL-USD"):
        try:
            values[product] = _returns(product)
        except PublicProviderError:
            if product == "BTC-USD":
                raise
    btc_return, btc_vol, observed = values["BTC-USD"]

    def relative(product: str) -> MetricObservation:
        if product in values:
            return MetricObservation.available(values[product][0] - btc_return, "percent")
        return MetricObservation.missing("percent", f"{product} candles unavailable")

    return MarketRegimeObservation(
        source="Coinbase Exchange",
        observed_at=observed,
        retrieved_at=retrieved,
        btc_return_30d_pct=MetricObservation.available(btc_return, "percent"),
        btc_realized_volatility_30d=MetricObservation.available(btc_vol, "annualized percent"),
        eth_relative_return_30d_pct=relative("ETH-USD"),
        sol_relative_return_30d_pct=relative("SOL-USD"),
        product_count=len(values),
    )
