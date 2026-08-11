from datetime import UTC, datetime

from src.models.observation import MetricObservation
from src.models.provisional import HolderOnChainObservation
from src.providers.http import PublicProviderError, get_json


def fetch_holder_onchain_observation() -> HolderOnChainObservation:
    payload = get_json(
        "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics",
        {"assets": "btc", "metrics": "CapMVRVCur,AdrActCnt", "frequency": "1d", "page_size": 100},
    )
    rows = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise PublicProviderError("invalid Coin Metrics payload")
    valid = sorted(
        (
            datetime.fromisoformat(row["time"].replace("Z", "+00:00")),
            float(row["CapMVRVCur"]),
            float(row["AdrActCnt"]),
        )
        for row in rows
        if isinstance(row, dict) and row.get("CapMVRVCur") and row.get("AdrActCnt")
    )
    if len(valid) < 31 or valid[-31][2] <= 0:
        raise PublicProviderError("insufficient Coin Metrics history")
    return HolderOnChainObservation(
        source="Coin Metrics Community",
        observed_at=valid[-1][0],
        retrieved_at=datetime.now(UTC),
        mvrv=MetricObservation.available(valid[-1][1], "ratio"),
        active_addresses_change_30d_pct=MetricObservation.available(
            (valid[-1][2] / valid[-31][2] - 1) * 100,
            "percent",
        ),
        history_points=len(valid),
    )
