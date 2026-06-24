"""Agent Visibility Audit: measured share of voice, diagnose, prescribe, before/after."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.environment import load_brand_data
from src.schema import BrandBlock, BrandData, ExperimentConfig, TreatmentArm
from src.treatments import (
    CITE_SOURCE_INSERT,
    PROBLEM_MATCH_PREFIX,
    QUOTATION_INSERT,
    footprint_has_statistic,
    treatment_description,
)

PRESCRIBABLE_ARMS: tuple[TreatmentArm, ...] = (
    "statistic",
    "cite_source",
    "quotation",
    "problem_match",
)

_ANALYZE_HINT = "Run `python run_experiment.py --analyze` first."


@dataclass
class AuditGap:
    """One diagnosed gap in the brand footprint."""

    dimension: str
    severity: float
    message: str
    suggested_arm: str


@dataclass
class ModelVisibility:
    """Measured agent share of voice for one model (control arm)."""

    model: str
    pick_rate: float
    ci_low: float
    ci_high: float
    picks: int
    reps: int


@dataclass
class Prescription:
    """Ranked fix recommendation from measured lift."""

    rank: int
    arm: str
    description: str
    lift: float
    lift_ci_low: float
    lift_ci_high: float
    resulting_pick_rate: float
    resulting_ci_low: float
    resulting_ci_high: float


@dataclass
class AuditReport:
    """Full audit output for one brand footprint and query regime."""

    brand_id: str
    brand_name: str
    query: str
    regime: str
    results_dir: str
    visibility: list[ModelVisibility]
    signals: dict[str, bool]
    gaps: list[AuditGap]
    prescriptions: dict[str, list[Prescription]]
    footprint_diagnostic: dict[str, float]


def load_pick_rates(results_dir: str | Path) -> pd.DataFrame:
    """Load pick_rates.csv; fail if missing."""
    path = Path(results_dir) / "pick_rates.csv"
    if not path.exists():
        raise FileNotFoundError(f"No pick_rates.csv in {results_dir}. {_ANALYZE_HINT}")
    return pd.read_csv(path)


def load_lifts(results_dir: str | Path) -> pd.DataFrame:
    """Load lift_vs_control.csv; fail if missing."""
    path = Path(results_dir) / "lift_vs_control.csv"
    if not path.exists():
        raise FileNotFoundError(f"No lift_vs_control.csv in {results_dir}. {_ANALYZE_HINT}")
    return pd.read_csv(path)


def _regime_label(results_dir: str | Path) -> str:
    """Derive a short regime label from the results directory name."""
    name = Path(results_dir).name
    if name == "results_q2":
        return "open"
    if name == "results":
        return "priced"
    return name


def detect_signals(
    block: BrandBlock,
    overrides: dict[str, str] | None = None,
) -> dict[str, bool]:
    """Return which treatment signals are present on the focal footprint."""
    page = block.brand_page
    editorial_text = " ".join(block.editorial)
    problem_prefix = (overrides or {}).get("problem_match", PROBLEM_MATCH_PREFIX)

    return {
        "statistic": footprint_has_statistic(page),
        "cite_source": CITE_SOURCE_INSERT in editorial_text
        or "Runner's World" in editorial_text,
        "quotation": QUOTATION_INSERT in editorial_text or "TechRadar" in editorial_text,
        "problem_match": page.lstrip().startswith(problem_prefix.strip()),
        "keyword_stuff": False,
    }


def score_visibility(pick_rates: pd.DataFrame, model: str) -> ModelVisibility:
    """Return measured control pick-rate + Wilson CI for one model."""
    row = pick_rates[(pick_rates["model"] == model) & (pick_rates["arm"] == "control")]
    if row.empty:
        raise ValueError(f"No control pick-rate for model {model!r} in pick_rates.csv")
    r = row.iloc[0]
    return ModelVisibility(
        model=model,
        pick_rate=float(r["pick_rate"]),
        ci_low=float(r["ci_low"]),
        ci_high=float(r["ci_high"]),
        picks=int(r["picks"]),
        reps=int(r["reps"]),
    )


def run_audit(
    config: ExperimentConfig,
    *,
    results_dir: str | Path | None = None,
    brand_id: str | None = None,
) -> AuditReport:
    """Score measured visibility, diagnose gaps, and prescribe ranked fixes."""
    out_dir = Path(results_dir or config.results_dir)
    pick_rates = load_pick_rates(out_dir)
    lifts_df = load_lifts(out_dir)

    data = load_brand_data(config.data_file)
    target_id = brand_id or config.focal
    block = data.brands[target_id]

    signals = detect_signals(block, config.treatment_overrides)
    gaps = diagnose_gaps(block, data, target_id)

    models = sorted(pick_rates["model"].unique())
    visibility = [score_visibility(pick_rates, model) for model in models]
    prescriptions = {
        model: prescribe_fixes(signals, lifts_df, pick_rates, model)
        for model in models
    }

    return AuditReport(
        brand_id=target_id,
        brand_name=block.name,
        query=config.query,
        regime=_regime_label(out_dir),
        results_dir=str(out_dir),
        visibility=visibility,
        signals=signals,
        gaps=gaps,
        prescriptions=prescriptions,
        footprint_diagnostic=_footprint_diagnostic(block, data, target_id),
    )


def diagnose_gaps(block: BrandBlock, data: BrandData, brand_id: str) -> list[AuditGap]:
    """Return template-based gap diagnoses from YAML footprint state."""
    gaps: list[AuditGap] = []
    page = block.brand_page.lower()

    if not block.editorial:
        gaps.append(
            AuditGap(
                dimension="trust",
                severity=0.9,
                message="No third-party editorial coverage — agents lack independent corroboration.",
                suggested_arm="cite_source",
            )
        )

    if not footprint_has_statistic(block.brand_page):
        gaps.append(
            AuditGap(
                dimension="trust",
                severity=0.75,
                message="Key claims lack hard numbers — battery and accuracy assertions are qualitative only.",
                suggested_arm="statistic",
            )
        )

    if "running" not in page or "sleep" not in page:
        gaps.append(
            AuditGap(
                dimension="reach",
                severity=0.7,
                message="Problem not named in description — running + sleep use case is implicit, not explicit.",
                suggested_arm="problem_match",
            )
        )

    source_count = 1 + len(block.reviews) + len(block.editorial)
    if source_count < 3:
        gaps.append(
            AuditGap(
                dimension="translation",
                severity=0.6,
                message=f"Thin source coverage ({source_count} blocks) — claim appears in too few independent places.",
                suggested_arm="coverage_dose",
            )
        )

    competitor_editorial = sum(
        1 for bid, comp in data.brands.items() if bid != brand_id and comp.editorial
    )
    if not block.editorial and competitor_editorial >= 3:
        gaps.append(
            AuditGap(
                dimension="translation",
                severity=0.85,
                message="Competitors have editorial picks; focal brand has none — visibility gap vs category norms.",
                suggested_arm="quotation",
            )
        )

    return sorted(gaps, key=lambda g: g.severity, reverse=True)


def prescribe_fixes(
    signals: dict[str, bool],
    lifts_df: pd.DataFrame,
    pick_rates: pd.DataFrame,
    model: str,
) -> list[Prescription]:
    """Rank absent signals by measured lift for this model; top-3, exclude keyword_stuff."""
    measured_arms = set(lifts_df[lifts_df["model"] == model]["arm"].astype(str))
    absent = [
        arm
        for arm in PRESCRIBABLE_ARMS
        if not signals.get(arm, False) and arm in measured_arms
    ]

    model_lifts = lifts_df[(lifts_df["model"] == model) & (lifts_df["arm"].isin(absent))].copy()
    model_lifts = model_lifts.sort_values("lift", ascending=False).head(3)

    prescriptions: list[Prescription] = []
    for rank, (_, row) in enumerate(model_lifts.iterrows(), start=1):
        arm = str(row["arm"])
        arm_rate = pick_rates[(pick_rates["model"] == model) & (pick_rates["arm"] == arm)]
        if arm_rate.empty:
            continue
        rate_row = arm_rate.iloc[0]
        prescriptions.append(
            Prescription(
                rank=rank,
                arm=arm,
                description=treatment_description(arm),  # type: ignore[arg-type]
                lift=round(float(row["lift"]), 3),
                lift_ci_low=round(float(row["lift_ci_low"]), 3),
                lift_ci_high=round(float(row["lift_ci_high"]), 3),
                resulting_pick_rate=round(float(rate_row["pick_rate"]), 3),
                resulting_ci_low=round(float(rate_row["ci_low"]), 3),
                resulting_ci_high=round(float(rate_row["ci_high"]), 3),
            )
        )
    return prescriptions


def run_before_after(
    config: ExperimentConfig,
    *,
    arm: str = "cite_source",
    results_dir: str | Path | None = None,
) -> dict[str, object]:
    """Derive control vs one treatment pick-rates per model from existing analysis."""
    out_dir = Path(results_dir or config.results_dir)
    pick_rates = load_pick_rates(out_dir)

    per_model: dict[str, dict[str, object]] = {}
    for model in sorted(pick_rates["model"].unique()):
        control = pick_rates[(pick_rates["model"] == model) & (pick_rates["arm"] == "control")]
        treatment = pick_rates[(pick_rates["model"] == model) & (pick_rates["arm"] == arm)]
        if control.empty or treatment.empty:
            continue
        c = control.iloc[0]
        t = treatment.iloc[0]
        before = float(c["pick_rate"])
        after = float(t["pick_rate"])
        per_model[model] = {
            "before_pick_rate": round(before, 3),
            "after_pick_rate": round(after, 3),
            "lift_pp": round(after - before, 3),
            "before_ci_low": round(float(c["ci_low"]), 3),
            "before_ci_high": round(float(c["ci_high"]), 3),
            "after_ci_low": round(float(t["ci_low"]), 3),
            "after_ci_high": round(float(t["ci_high"]), 3),
            "reps": int(t["reps"]),
        }

    return {
        "arm": arm,
        "query": config.query,
        "regime": _regime_label(out_dir),
        "per_model": per_model,
    }


def write_audit_report(report: AuditReport, out_dir: str | Path) -> Path:
    """Write audit report to JSON and markdown."""
    path = Path(out_dir)
    path.mkdir(parents=True, exist_ok=True)

    payload = {
        "brand_id": report.brand_id,
        "brand_name": report.brand_name,
        "query": report.query,
        "regime": report.regime,
        "results_dir": report.results_dir,
        "visibility": [
            {
                "model": v.model,
                "share_of_voice": v.pick_rate,
                "ci_low": v.ci_low,
                "ci_high": v.ci_high,
                "picks": v.picks,
                "reps": v.reps,
            }
            for v in report.visibility
        ],
        "signals": report.signals,
        "gaps": [
            {
                "dimension": g.dimension,
                "severity": g.severity,
                "message": g.message,
                "suggested_arm": g.suggested_arm,
            }
            for g in report.gaps
        ],
        "prescriptions": {
            model: [
                {
                    "rank": p.rank,
                    "arm": p.arm,
                    "description": p.description,
                    "lift_pp": p.lift,
                    "lift_ci_low": p.lift_ci_low,
                    "lift_ci_high": p.lift_ci_high,
                    "resulting_pick_rate": p.resulting_pick_rate,
                    "resulting_ci_low": p.resulting_ci_low,
                    "resulting_ci_high": p.resulting_ci_high,
                }
                for p in rxs
            ]
            for model, rxs in report.prescriptions.items()
        },
        "footprint_diagnostic": report.footprint_diagnostic,
    }

    json_path = path / "audit_report.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    md_lines = [
        f"# Agent Visibility Audit — {report.brand_name}",
        "",
        f"**Query:** {report.query}",
        f"**Regime:** {report.regime} (`{report.results_dir}`)",
        "",
        "## Agent share of voice (measured)",
        "",
        "| Model | Pick-rate | 95% CI |",
        "|---|---|---|",
    ]
    for v in report.visibility:
        md_lines.append(
            f"| {v.model} | {v.pick_rate:.0%} | {v.ci_low:.0%}–{v.ci_high:.0%} |"
        )

    md_lines.extend(["", "## Signals (present / absent)", ""])
    for arm, present in sorted(report.signals.items()):
        status = "present" if present else "absent"
        md_lines.append(f"- **{arm}**: {status}")

    md_lines.extend(["", "## Gaps (footprint diagnostic)", ""])
    for gap in report.gaps:
        md_lines.append(f"- **[{gap.dimension.upper()}]** {gap.message}")

    for model, rxs in report.prescriptions.items():
        md_lines.extend(["", f"## Prescribed fixes — {model}", ""])
        for rx in rxs:
            md_lines.append(
                f"{rx.rank}. **{rx.arm}** — {rx.description} "
                f"(lift {rx.lift:+.0%}, CI {rx.lift_ci_low:+.0%}–{rx.lift_ci_high:+.0%}; "
                f"→ {rx.resulting_pick_rate:.0%} pick-rate)"
            )

    diag = report.footprint_diagnostic
    md_lines.extend(
        [
            "",
            "## Footprint diagnostic (not measured visibility)",
            "",
            f"| Reach | Trust | Translation |",
            f"|---|---|---|",
            f"| {diag['reach']} | {diag['trust']} | {diag['translation']} |",
        ]
    )

    md_path = path / "audit_report.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    return json_path


def _footprint_diagnostic(block: BrandBlock, data: BrandData, brand_id: str) -> dict[str, float]:
    """Legacy heuristic scores — labelled diagnostic only, not agent visibility."""
    reach = _score_reach(block)
    trust = _score_trust(block)
    translation = _score_translation(block, data, brand_id)
    return {
        "reach": reach,
        "trust": trust,
        "translation": translation,
    }


def _score_reach(block: BrandBlock) -> float:
    """Score Reach dimension from footprint heuristics."""
    score = 40.0
    page = block.brand_page.lower()
    if "running" in page:
        score += 15
    if "sleep" in page:
        score += 15
    if block.price <= 250:
        score += 10
    if len(block.reviews) >= 2:
        score += 10
    return min(100.0, score)


def _score_trust(block: BrandBlock) -> float:
    """Score Trust dimension from corroboration signals."""
    score = 30.0
    score += min(30.0, len(block.editorial) * 15)
    score += min(15.0, len(block.reviews) * 7)
    if footprint_has_statistic(block.brand_page):
        score += 20
    return min(100.0, score)


def _score_translation(block: BrandBlock, data: BrandData, brand_id: str) -> float:
    """Score Translation dimension from cross-source coverage."""
    source_count = 1 + len(block.reviews) + len(block.editorial)
    score = 25.0 + source_count * 12
    competitors_with_editorial = sum(
        1 for bid, comp in data.brands.items() if bid != brand_id and comp.editorial
    )
    if not block.editorial and competitors_with_editorial >= 2:
        score -= 20
    return max(0.0, min(100.0, score))
