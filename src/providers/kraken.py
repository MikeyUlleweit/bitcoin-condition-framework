from datetime import UTC, datetime, timedelta
from typing import Any

from src.models.observation import MetricObservation
from src.models.provisional import LeverageObservation
from src.providers.http import PublicProviderError, get_json


def _series(kind: str) -> tuple[Any, datetime]:
    since = int((datetime.now(UTC) - timedelta(days=35)).timestamp())
    payload = get_json(
        f"https://futures.kraken.com/api/charts/v1/analytics/PF_XBTUSD/{kind}",
        {"since": since, "interval": 86400},
    )
    if (
        not isinstance(payload, dict)
        or payload.get("errors")
        or not isinstance(payload.get("result"), dict)
    ):
        raise PublicProviderError(f"invalid Kraken {kind} payload")
    result = payload["result"]
    timestamps = result.get("timestamp")
    if not isinstance(timestamps, list) or not timestamps:
        raise PublicProviderError(f"missing Kraken {kind} timestamps")
    epoch = int(timestamps[-1])
    if epoch > 10_000_000_000:
        epoch //= 1000
    return result.get("data"), datetime.fromtimestamp(epoch, tz=UTC)


def fetch_leverage_observation() -> LeverageObservation:
    funding_data, observed = _series("funding")
    oi_data, _ = _series("open-interest")
    basis_data, _ = _series("future-basis")
    try:
        funding = [float(row[3]) * 100 for row in funding_data["relativeRate"]]
        oi = [float(row[3]) for row in oi_data]
        basis = float(basis_data["basis"][-1]) * 100
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise PublicProviderError("incomplete Kraken leverage history") from exc
    if not funding or len(oi) < 2 or oi[0] <= 0:
        raise PublicProviderError("insufficient Kraken leverage history")
    return LeverageObservation(
        source="Kraken Futures",
        observed_at=observed,
        retrieved_at=datetime.now(UTC),
        funding_rate_30d_avg_pct=MetricObservation.available(
            sum(funding) / len(funding), "percent"
        ),
        open_interest_change_30d_pct=MetricObservation.available(
            (oi[-1] / oi[0] - 1) * 100, "percent"
        ),
        futures_basis_pct=MetricObservation.available(basis, "percent"),
        history_points=min(len(funding), len(oi)),
    )
