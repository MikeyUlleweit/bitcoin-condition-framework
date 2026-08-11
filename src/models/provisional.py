from typing import Literal

from pydantic import Field

from src.models.observation import MetricObservation, ObservationBase


class MarketRegimeObservation(ObservationBase):
    observation_type: Literal["market_regime"] = "market_regime"
    btc_return_30d_pct: MetricObservation
    btc_realized_volatility_30d: MetricObservation
    eth_relative_return_30d_pct: MetricObservation
    sol_relative_return_30d_pct: MetricObservation
    product_count: int = Field(..., ge=0, le=3)

class MinerEconomicsObservation(ObservationBase):
    observation_type: Literal["miner_economics"] = "miner_economics"
    hashrate_change_30d_pct: MetricObservation
    difficulty_adjustment_pct: MetricObservation
    fee_share_of_rewards_pct: MetricObservation
    history_points: int = Field(..., ge=0)

class LeverageObservation(ObservationBase):
    observation_type: Literal["leverage"] = "leverage"
    funding_rate_30d_avg_pct: MetricObservation
    open_interest_change_30d_pct: MetricObservation
    futures_basis_pct: MetricObservation
    history_points: int = Field(..., ge=0)

class HolderOnChainObservation(ObservationBase):
    observation_type: Literal["holder_onchain"] = "holder_onchain"
    mvrv: MetricObservation
    active_addresses_change_30d_pct: MetricObservation
    history_points: int = Field(..., ge=0)
