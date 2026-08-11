from typing import Literal

from src.models.observation import MetricObservation, ObservationBase


class BlockspaceObservation(ObservationBase):
    observation_type: Literal["blockspace"] = "blockspace"
    fastest_fee: MetricObservation
    half_hour_fee: MetricObservation
    hour_fee: MetricObservation
    economy_fee: MetricObservation
    minimum_fee: MetricObservation
    mempool_count: MetricObservation
    mempool_vsize: MetricObservation
    mempool_total_fee: MetricObservation
