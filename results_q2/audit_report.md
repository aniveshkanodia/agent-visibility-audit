# Agent Visibility Audit — Amazfit Active

**Query:** Recommend a smartwatch for running and sleep tracking.
**Regime:** open (`results_q2`)

## Agent share of voice (measured)

| Model | Pick-rate | 95% CI |
|---|---|---|
| claude-haiku-4-5 | 13% | 5%–30% |
| gemini-3.5-flash | 0% | 0%–11% |

## Signals (present / absent)

- **cite_source**: absent
- **keyword_stuff**: absent
- **problem_match**: absent
- **quotation**: absent
- **statistic**: absent

## Gaps (footprint diagnostic)

- **[TRUST]** No third-party editorial coverage — agents lack independent corroboration.
- **[TRANSLATION]** Competitors have editorial picks; focal brand has none — visibility gap vs category norms.
- **[TRUST]** Key claims lack hard numbers — battery and accuracy assertions are qualitative only.

## Prescribed fixes — claude-haiku-4-5

1. **quotation** — Adds TechRadar quote endorsement to editorial. (lift +60%, CI +26%–+80%; → 73% pick-rate)
2. **problem_match** — Prefixes description with running + sleep + under-$250 framing. (lift +47%, CI +13%–+70%; → 60% pick-rate)
3. **cite_source** — Adds third-party Runner's World citation to editorial. (lift +33%, CI +1%–+58%; → 47% pick-rate)

## Prescribed fixes — gemini-3.5-flash

1. **statistic** — Adds hard-number lab statistics to brand page. (lift +10%, CI -8%–+26%; → 10% pick-rate)
2. **problem_match** — Prefixes description with running + sleep + under-$250 framing. (lift +3%, CI -11%–+17%; → 3% pick-rate)
3. **cite_source** — Adds third-party Runner's World citation to editorial. (lift +0%, CI -11%–+11%; → 0% pick-rate)

## Footprint diagnostic (not measured visibility)

| Reach | Trust | Translation |
|---|---|---|
| 90.0 | 44.0 | 41.0 |