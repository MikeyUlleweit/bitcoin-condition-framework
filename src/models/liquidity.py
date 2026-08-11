from typing import Literal, Self

from pydantic import Field, model_validator

from src.models.observation import MetricObservation, ObservationBase


class LiquidityObservation(ObservationBase):
    observation_type: Literal["liquidity"] = "liquidity"
    defi_tvl: MetricObservation
    chain_count: int = Field(..., ge=0)
    valid_chain_count: int = Field(..., ge=0)
    invalid_chain_count: int = Field(..., ge=0)
    stablecoin_supply: MetricObservation = Field(
        default_factory=lambda: MetricObservation.missing(
            "USD", "stablecoin history not collected"
        )
    )
    stablecoin_supply_30d_ago: MetricObservation = Field(
        default_factory=lambda: MetricObservation.missing(
            "USD", "stablecoin history not collected"
        )
    )
    stablecoin_change_30d_pct: MetricObservation = Field(
        default_factory=lambda: MetricObservation.missing(
            "percent", "stablecoin history not collected"
        )
    )
    stablecoin_history_points: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_chain_counts(self) -> Self:
        if self.valid_chain_count + self.invalid_chain_count != self.chain_count:
            raise ValueError("valid and invalid chain counts must equal chain_count")
        return self
