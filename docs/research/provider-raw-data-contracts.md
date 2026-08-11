# Raw Provider Contract Research

Scope: the external endpoints that are actually called by production code as of
2026-08-11. Configuration-only providers and empty provider modules are excluded.

## mempool.space

### `GET /api/v1/fees/recommended`

- The endpoint returns mempool.space's current suggested fees for new
  transactions. The official REST reference names the endpoint, but does not
  specify a response schema, field-level confirmation targets, or missing-field
  behavior. ([mempool.space REST API](https://mempool.space/docs/api/rest))
- The live response currently contains `fastestFee`, `halfHourFee`, `hourFee`,
  `economyFee`, and `minimumFee`. These are fee-rate recommendations (commonly
  expressed in sat/vB), but that unit and the time/confirmation semantics of
  each named tier are not stated in the official REST reference. The raw-data
  contract should therefore avoid treating the names as guaranteed confirmation
  deadlines unless mempool.space publishes that guarantee.
- The response has no observation timestamp. A validated observation must attach
  a client-side `observed_at` timestamp and retain provider/source identity; it
  cannot infer provider event time from this payload.
- The official docs warn that rate limiting produces HTTP `429`. They do not
  document endpoint-specific empty, partial, or error bodies. A contract should
  treat non-2xx responses, invalid JSON, non-object JSON, absent required fields,
  and non-numeric values as explicit failures rather than as zero.

### `GET /api/mempool`

- The endpoint is the current mempool backlog, with `count` = transaction count,
  `vsize` = total virtual bytes, `total_fee` = total fees in satoshis, and
  `fee_histogram` = `(feerate, vsize)` buckets. Each bucket's vsize covers
  transactions below the previous bucket's fee rate and above the current one.
  ([mempool.space REST API](https://mempool.space/docs/api/rest),
  [upstream Esplora API specification](https://github.com/Blockstream/esplora/blob/master/API.md#mempool))
- `fee_histogram` fee rates are sat/vB and bucket sizes are virtual bytes, as
  shown by the upstream specification's worked example. `count`, `vsize`, and
  `total_fee` are aggregate snapshot values, not time series.
- The payload has no observation timestamp. As with recommended fees, collection
  time must be supplied by the client and must not be confused with a provider
  event timestamp.
- No official endpoint-specific null/partial-response semantics are published.
  Missing required aggregates must be represented as unavailable/error, never
  silently dropped or converted to zero.

## DeFiLlama

### `GET /v2/chains`

- This is a free, unauthenticated endpoint at `https://api.llama.fi/v2/chains`
  for current TVL across all chains. The documented response is an array of
  objects with `gecko_id`, `tvl`, `tokenSymbol`, `cmcId`, `name`, and `chainId`.
  ([DefiLlama free API reference](https://api-docs.defillama.com/llms-free.txt))
- For a chain, TVL means the sum of protocol TVL on that chain; protocol TVL is
  the value of coins held in protocol smart contracts. DefiLlama excludes or
  separates several categories (including native staking, bridge TVL attributed
  to chains, and double-counted receipt-token value), so this is not a measure of
  all capital or liquidity on a chain. ([DefiLlama data definitions](https://docs.llama.fi/analysts/data-definitions),
  [DefiLlama methodology](https://docs.llama.fi/))
- DefiLlama presents chain TVL as a currency value in dollars, but its endpoint
  schema only calls the field `tvl` and does not explicitly declare the unit in
  the free API reference. The application should record the intended unit as a
  contract decision and protect it with a fixture/contract test rather than rely
  only on the bare field name.
- The response contains no timestamp or as-of field. A consumer can establish
  collection time, but cannot establish provider computation time or freshness
  from this response alone.
- The free API reference does not publish nullability, omission rules, error-body
  schemas, or completeness guarantees for `/v2/chains`. A chain item missing
  `name` or a numeric `tvl` should be rejected/quarantined explicitly. An empty
  array must not be interpreted as zero total TVL.

## Contract implications for this repository

1. Raw responses need endpoint-specific validation before feature calculation;
   coercing arbitrary values with `int(...)` or skipping malformed entries hides
   provider-contract failures.
2. Observations need explicit source, endpoint, unit, and client collection time.
   These three endpoints provide no provider-side observation timestamp.
3. Missing, malformed, partial, empty, rate-limited, and transport-failure states
   must remain distinguishable. None is equivalent to a measured zero.
4. `fee_histogram` is structured source data and should not be discarded at the
   provider boundary if later explainable congestion features may require it.
5. Summing every numeric `tvl` from `/v2/chains` is an application aggregation,
   not a separately documented DeFiLlama metric. Its duplicate/category semantics
   should be verified before that sum is treated as a canonical market feature.
