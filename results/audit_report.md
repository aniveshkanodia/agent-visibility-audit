# Agent Visibility Audit — Amazfit Active

**Query:** Recommend a smartwatch for running and sleep tracking under $250.
**Regime:** priced (`results`)

## Agent share of voice (measured)

| Model | Pick-rate | 95% CI |
|---|---|---|
| claude-haiku-4-5 | 10% | 2%–40% |
| gemini-3.5-flash | 50% | 24%–76% |

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

1. **problem_match** — Prefixes description with running + sleep + under-$250 framing. (lift +80%, CI +19%–+96%; → 90% pick-rate)
2. **quotation** — Adds TechRadar quote endorsement to editorial. (lift +80%, CI +19%–+96%; → 90% pick-rate)
3. **cite_source** — Adds third-party Runner's World citation to editorial. (lift +70%, CI +9%–+92%; → 80% pick-rate)

## Prescribed fixes — gemini-3.5-flash

1. **cite_source** — Adds third-party Runner's World citation to editorial. (lift +50%, CI -4%–+76%; → 100% pick-rate)
2. **problem_match** — Prefixes description with running + sleep + under-$250 framing. (lift +50%, CI -4%–+76%; → 100% pick-rate)
3. **quotation** — Adds TechRadar quote endorsement to editorial. (lift +50%, CI -4%–+76%; → 100% pick-rate)

## Footprint diagnostic (not measured visibility)

| Reach | Trust | Translation |
|---|---|---|
| 90.0 | 44.0 | 41.0 |