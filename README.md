# Agent Visibility Audit — PMG Hackathon 2026

When a shopper asks an AI to recommend a smartwatch, what in the brand's online information actually drives the pick? We change one element of **Amazfit Active's** footprint at a time, hold rivals and the question constant, and measure pick-rate across two AI models.

**Agent Visibility Audit report:** [aniveshkanodia.github.io/agent-visibility-audit](https://aniveshkanodia.github.io/agent-visibility-audit/)

**Category:** smartwatches · **Focal brand:** Amazfit Active · **Models:** Claude Haiku 4.5, Gemini 3.5 Flash

---

## Key findings (measured pick-rates)

Numbers below come from frozen runs in [`results/`](results/) and [`results_q2/`](results_q2/). Reported **per model** — never pooled.

1. **Outside proof raises picks (priced query, n=10).** On Claude, a press citation moved Amazfit from **10% → 80%** baseline pick-rate; naming the buyer's need hit **90%**. Gemini started higher (**50%** baseline) and saturated near **100%** on most edits — it was responding to price fit, not footprint quality.

2. **Visibility is contextual (open query, n=30).** Remove the "$250" ceiling and Amazfit's price edge disappears. Claude baseline **13%**; expert quote lifts to **73%**, press citation to **47%**. Gemini stays **0%** across all footprint edits — it keeps picking Garmin (the category's editorial winner).

3. **Agents reach for outside proof when it exists.** When a press block is present, the model cites it in nearly every run where it picks Amazfit (`cited_sources` in `runs.csv`). Self-reported confidence barely moves — pick-rate is the real signal.

---

## Frozen results

| Directory | Query | Reps | Claude baseline | Gemini baseline |
|---|---|---|---|---|
| [`results/`](results/) | Recommend a smartwatch for running and sleep tracking under $250. | 10/arm | 10% | 50% |
| [`results_q2/`](results_q2/) | Recommend a smartwatch for running and sleep tracking. | 30/arm | 13% | 0% |

Each directory contains `runs.csv`, analysis tables, lift charts (`*.png`), and `audit_report.md` (measured visibility + footprint diagnostic).

---

## Quick start

Requires [uv](https://docs.astral.sh/uv/). Frozen results are already committed — you can analyze and audit without API keys:

```bash
uv sync
uv run python run_experiment.py --analyze
uv run python run_experiment.py --audit
```

To re-run agents (needs keys in `.env`):

```bash
cp .env.example .env   # set ANTHROPIC_API_KEY and/or GEMINI_API_KEY
uv run python run_experiment.py --reps 10
uv run python run_experiment.py --analyze
uv run python run_experiment.py --audit
```

### Reproduce open query (q2)

```bash
uv run python run_experiment.py --config config/experiment_q2.yaml --analyze
uv run python run_experiment.py --config config/experiment_q2.yaml --audit
```

Re-running the full q2 matrix: add `--reps 30` without `--analyze`/`--audit` (API keys required).

---

## Project layout

| Path | Purpose |
|---|---|
| `config/experiment.yaml` | Priced query experiment (→ `results/`) |
| `config/experiment_q2.yaml` | Open query experiment (→ `results_q2/`) |
| `data/smartwatches.yaml` | Curated brand footprint blocks |
| `data/prompts/` | Agent prompt templates |
| `src/` | Harness: environment, treatments, runner, analyze, audit |
| `run_experiment.py` | CLI entry point |
| `results/`, `results_q2/` | **Frozen submission runs** (committed) |
| `index.html` | Interactive findings app (GitHub Pages) |

---

## Method (honest limits)

- **Controlled information package:** agents reason over curated product cards (post-retrieval bundle), not live web browsing — required to isolate one variable at a time.
- **Small samples:** n=10 (priced) and n=30 (open); treat single-arm gains as directional where CIs are wide.
- **Brand-safe:** every treatment is a signal a brand could truthfully earn in public; keyword stuffing is measured as a caution, never prescribed.

---

## License

MIT — see [LICENSE](LICENSE). Experiment code only; treatment stimuli in `src/treatments.py` are synthetic placeholders for controlled testing.
