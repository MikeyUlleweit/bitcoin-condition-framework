from enum import StrEnum


class SignalCategory(StrEnum):
    LIQUIDITY = "Liquidity Condition"
    MINER = "Miner Condition"
    HOLDER = "Holder Condition"
    LEVERAGE = "Leverage Condition"
    BLOCKSPACE = "Blockspace / Network Demand"
    MARKET_REGIME = "Market Regime / Rotation"
