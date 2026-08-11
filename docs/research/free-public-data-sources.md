# Free and Public Data Sources for Bitcoin Condition Signals

Research date: 2026-08-11. This note evaluates sources against the repository's
six signal categories. "Free" does not mean production-SLA data: rate limits,
licenses, geographic availability, and schema drift still need explicit handling.

## Bottom line

Most categories can be made **research-scoreable** with public data, but not by
simply filling the existing empty components. The strongest zero-license-cost
path is:

1. mempool.space and/or a local Bitcoin Core node for blockspace and mining;
2. DefiLlama's stablecoin history for one liquidity component;
3. Kraken Futures analytics (with Binance as a second venue) for
   exchange-specific leverage;
4. Coin Metrics Community data or a self-hosted Bitcoin Research Kit node for
   holder/on-chain features;
5. Coinbase Exchange public candles (and optionally CoinGecko) for price regime
   and crypto rotation.

Each source has a different universe. A Binance funding score is **Binance
BTCUSDT leverage**, not global leverage. DefiLlama stablecoin supply is one
liquidity component, not dollar liquidity. Those scope labels must survive into
every observation and score.

## Access classes

- **Public/no auth:** callable without an account or API key, normally subject
  to IP rate limits and no SLA.
- **Free tier:** registration/key required; quotas or history restrictions apply.
- **Self-hosted:** source data is public and software is open source, but the
  operator bears node, storage, indexing, and validation costs.
- **Paid:** useful for comparison, but not a dependency for a free-data build.

## Source matrix

| Category | Source and access | Useful fields/history | Assessment |
|---|---|---|---|
| Blockspace | [mempool.space REST API](https://mempool.space/docs/api/rest), public/no auth | Current mempool count, vsize, total fees and fee histogram; recommended fee rates; projected blocks. Mining endpoints expose historical block fee rates, fees, sizes/weights, rewards and difficulty/hashrate over documented trailing windows up to three years. | **Scoreable now.** Archive current mempool observations because current endpoints are snapshots. Use mined-block series for historical calibration, not retroactively reconstructed mempool snapshots. |
| Blockspace | [Bitcoin Core RPC](https://bitcoincore.org/en/doc/), self-hosted | `getmempoolinfo`, `getrawmempool`, `getblockstats`, chain and transaction data. Full chain history is locally reproducible; mempool history exists only from collection onward. | **Best provenance/control**, but requires operating a node and retaining snapshots. |
| Liquidity | [DefiLlama official SDK](https://github.com/DefiLlama/api-sdk), public/no auth for listed free modules | Stablecoin current market caps, combined historical market cap, per-chain history, individual stablecoin history and prices; historical chain TVL is also free. | **Stablecoin supply is scoreable after contract validation.** TVL is contextual, not a dollar-liquidity measure. The SDK marks stablecoin dominance and ETF data as Pro. |
| Liquidity | [Kraken Futures Market Analytics](https://docs.kraken.com/api/docs/futures-api/charts/market-analytics), public/no auth | Historical bucketed order-book, spread, liquidity and slippage analytics with `since`, `to`, `interval` and paginated `more` responses. | **Scoreable as venue liquidity**, with the venue and contract retained in the observation. It is not global BTC depth. |
| Liquidity | [FRED series observations](https://fred.stlouisfed.org/docs/api/fred/series_observations.html), free registered API key | Macro series observations; FRED/ALFRED supports vintage/revision-aware queries through documented real-time periods. | Useful for a separately defined macro-liquidity component. Series selection and publication lag must be modeled; never forward-fill unreleased observations into a backtest. |
| Liquidity | [Coin Metrics Community API](https://docs.coinmetrics.io/api), public/no auth | Community asset metrics and market prices, daily archives; 10 requests per 6 seconds/IP. Exact free metric coverage is discoverable through the community catalog and may change. | Potential corroboration. Query/catalog-pin exact metrics before design; do not assume a metric in the general encyclopedia is Community-accessible. |
| Leverage | [Binance USD-M Futures market data](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api), public market endpoints | BTCUSDT perpetual funding history, premium/index/mark price, current OI, OI statistics, taker ratios, long/short ratios, liquidations and basis depending on endpoint. Binance documents only the latest 30 days for several statistics endpoints; funding history is pageable. | **Scoreable as an exchange-specific component.** Backfill immediately and archive continuously. Never label it global OI or global leverage. Availability may vary by jurisdiction. |
| Leverage | [Kraken Futures Market Analytics](https://docs.kraken.com/api/docs/futures-api/charts/market-analytics), public/no auth | Historical bucketed open interest, funding, futures basis, liquidation volume, long/short ratios, CVD and volatility, with time ranges and pagination. | **Best documented free first venue** for a leverage score. Still venue-specific. Kraken's separate public trade-history endpoint documents only recent history, so use the analytics endpoint and archive raw responses. |
| Miner | [mempool.space mining API](https://mempool.space/docs/api/rest), public/no auth | Network hashrate/difficulty, difficulty adjustments, mining-pool shares, block fees and rewards, with trailing periods generally up to three years. | **Scoreable now** for hash-rate trend, difficulty trend and fee share of miner revenue, subject to validating returned schemas/units. Pool attribution is heuristic and should not be treated as consensus fact. |
| Miner | [Bitcoin Core RPC](https://bitcoincore.org/en/doc/), self-hosted | `getnetworkhashps`, `getdifficulty`, `getblockstats` and block subsidy/fee data derived from the canonical chain. | **Strong reproducible source.** Estimated hash rate is derived from block arrival and difficulty, not direct measurement of miners. |
| Holder/on-chain | [Coin Metrics Community API](https://docs.coinmetrics.io/api), public/no auth; [daily Community CSV archive](https://github.com/coinmetrics/data) | Daily BTC network metrics, timestamps and metric-status metadata. The official archive is rebuilt daily from the free Community tier and contains all currently free BTC metrics; history generally reaches metric inception. | **Likely quickest research path.** Pin the selected metric IDs, definitions, license (CC BY-NC 4.0), minimum times and status fields from the live community catalog. Do not infer that Pro-only MVRV/SOPR/cohort metrics are free. |
| Holder/on-chain | [Bitcoin Research Kit](https://github.com/bitcoinresearchkit/brk), self-hosted; its README identifies Bitview as a free hosted instance | Full-chain indexed supply distributions, holder cohorts, realized cap, MVRV, SOPR, NVT and thousands of other metrics at multiple resolutions. | **Strongest fully reproducible long-term option**, but operationally heavier and newer. Validate definitions and point-in-time behavior before using the hosted instance or derived metrics in calibrated scores. |
| Market regime/rotation | [Coinbase Exchange market-data API](https://docs.cdp.coinbase.com/exchange/introduction/welcome), public/no auth | Public spot trades/books and product candles. Candles provide time, OHLC and volume at 1m through 1d granularities, max 300 per request; Coinbase warns gaps occur where there are no ticks. | **Scoreable now** for BTC trend/volatility and a defined set of alt/BTC or alt/USD pairs. Persist the product universe and missing candles explicitly. |
| Market regime/rotation | [CoinGecko keyless public API](https://docs.coingecko.com/docs/keyless-public-api), public/no auth; [free Demo REST](https://docs.coingecko.com/docs/data-delivery-methods), key required | Broad-asset price, volume and market-cap data; historical endpoints exist. Public access is dynamically IP-throttled and intended for light/non-commercial experimentation; free Demo has credits/quotas. | Useful for broad crypto breadth/dominance research, but **not a production-quality dependency without a keyed plan or local archive**. Archive observations and record universe membership to avoid survivorship bias. |

## Category-specific recommendations

### 1. Blockspace

Keep the existing mempool.space path, but expand it with the documented mining
fee-rate and block size/weight history. Calibrate congestion features on mined
block history while accumulating genuine point-in-time mempool snapshots.
Recommended initial components: backlog vbytes, fee histogram pressure,
recommended-fee spread, mined-block utilization and fee-rate percentiles.

### 2. Liquidity

Replace aggregate chain TVL as a score input with DefiLlama's all-stablecoin
historical market cap series. Features such as 7/30/90-day supply change can be
tested as crypto-native liquidity proxies. Keep TVL visible only as context.
ETF flows are not free in DefiLlama's official SDK, and no reviewed official
public source here provides a complete normalized ETF-flow history.

### 3. Leverage

Implement a scoped Kraken perpetual/futures observation first: funding, OI,
basis and liquidation imbalance from its historical Market Analytics API. Add a
separate `binance_btcusdt_perpetual` observation as a second venue: funding, OI,
premium/basis and liquidation/taker imbalance where documented. Binance's
historical endpoint limits make immediate archival important. A robust "global
leverage" score still needs explicitly weighted multiple venues or a paid
aggregator; never silently relabel one venue as the market.

### 4. Miner

mempool.space already exposes enough history for a first miner stress/activity
score: hashrate and difficulty trends plus transaction-fee share of block reward.
Cross-check formulas against Bitcoin Core. Miner-to-exchange flows and miner
wallet balances require entity labeling and are not justified by these public
consensus-level sources; leave them unavailable rather than substitute pool
shares or raw coinbase outputs.

### 5. Holder/on-chain

Use Coin Metrics Community first if its live catalog exposes the precisely
defined metrics selected by the model. The API is keyless and its official CSV
archive is practical for initial backfill, but the non-commercial license must
be reviewed before eventual commercial algorithm use. For maximum independence,
evaluate BRK behind the same observation contract and reproduce features from a
local Bitcoin Core node. Address counts are not holder counts, and address
balances must never be described as investor cohorts without entity heuristics.

### 6. Market regime/rotation

Use Coinbase public daily/hourly candles for deterministic BTC trend,
drawdown, realized volatility and spot-volume features. Define rotation as a
fixed, versioned asset universe (for example, liquid Coinbase alt/BTC products)
rather than today's top-N list. CoinGecko can add market-cap breadth, but changing
listings create survivorship bias unless historical membership is stored.

## Weak proxies that should remain unscored

- Total DeFi TVL as "global liquidity" or stablecoin liquidity.
- One exchange's open interest/funding as global derivatives leverage.
- Mining-pool share as miner financial health or miner selling pressure.
- Active addresses, address counts, or large addresses as unique holders/whales.
- Raw exchange inflows without controlled address/entity labels.
- Today's top-N coins replayed backward as historical market breadth.
- Fear-and-greed composites whose weights, history, or upstream inputs are not
  fully specified and reproducible.
- Search interest, social sentiment, or API display scores as substitutes for
  price/on-chain observations.
- Current public snapshots used as if they were historical observations.

## Commercial/free-tier boundaries to preserve

- Coin Metrics Community is keyless and rate-limited, but much of the wider
  Coin Metrics catalog is Pro. Use the community catalog endpoint as the source
  of truth for actual entitlement.
- DefiLlama's official SDK marks ETFs, stablecoin dominance, yields/perpetual
  funding, bridges and several other modules as Pro even though stablecoin market
  cap/history and TVL history are free.
- CoinGecko's keyless API is intended for light experimentation; Demo is a
  registered free tier and both are quota/reliability constrained.
- Coinbase Exchange market data is public, but REST historical candles are
  capped at 300 per call and may contain gaps.
- Binance public derivatives history is fragmented by endpoint and several
  statistics endpoints expose only recent history. Local archival is mandatory.

## Recommended implementation order

1. DefiLlama stablecoin-supply observation and historical change features.
2. Coinbase BTC price-regime observation and features.
3. mempool.space miner observation using hashrate/difficulty/reward series.
4. Kraken-scoped leverage observation, then Binance as a distinct second venue,
   with immediate archival of both.
5. Coin Metrics Community catalog audit, then selected holder features.
6. Versioned crypto universe and rotation/breadth features.
7. Parallel research spike for BRK/self-hosted full-node reproducibility.

Before any score is enabled, add frozen provider fixtures, units, source scope,
event/retrieval timestamps, missingness rules, minimum-history requirements and
an out-of-sample calibration note. A free endpoint makes a feature available; it
does not make the feature predictive.
