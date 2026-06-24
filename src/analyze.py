"""Pick-rate analysis, lift vs control, Wilson CIs, and charts."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.schema import ExperimentConfig


def _safe_model_slug(model: str) -> str:
    """Sanitize model id for filesystem-safe chart filenames."""
    return model.replace("/", "_").replace("\\", "_")


def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Return Wilson score 95% confidence interval for a proportion."""
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    denom = 1.0 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = z * np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def load_runs(results_dir: str | Path) -> pd.DataFrame:
    """Load run records from CSV or JSON in results_dir."""
    results_path = Path(results_dir)
    csv_path = results_path / "runs.csv"
    json_path = results_path / "runs.json"

    if csv_path.exists():
        df = pd.read_csv(csv_path)
        for col in ("brand_order", "ranked_list", "cited_sources"):
            if col in df.columns and df[col].dtype == object:
                df[col] = df[col].apply(
                    lambda val: json.loads(val) if isinstance(val, str) and val.startswith("[") else val
                )
        return df

    if json_path.exists():
        records = json.loads(json_path.read_text(encoding="utf-8"))
        return pd.DataFrame(records)

    raise FileNotFoundError(f"No runs.csv or runs.json found in {results_path}")


def compute_pick_rates(df: pd.DataFrame) -> pd.DataFrame:
    """Compute focal pick-rate per model and arm."""
    grouped = (
        df.groupby(["model", "arm"], as_index=False)
        .agg(picks=("focal_picked", "sum"), reps=("focal_picked", "count"))
    )
    grouped["pick_rate"] = grouped["picks"] / grouped["reps"]
    cis = grouped.apply(
        lambda row: wilson_ci(int(row["picks"]), int(row["reps"])),
        axis=1,
    )
    grouped["ci_low"] = cis.apply(lambda pair: pair[0])
    grouped["ci_high"] = cis.apply(lambda pair: pair[1])
    return grouped


def compute_lift(summary: pd.DataFrame) -> pd.DataFrame:
    """Compute lift vs control per model with Wilson CIs on the difference."""
    rows: list[dict[str, float | str]] = []
    for model in summary["model"].unique():
        model_df = summary[summary["model"] == model]
        control_rows = model_df[model_df["arm"] == "control"]
        if control_rows.empty:
            continue
        control = control_rows.iloc[0]
        control_rate = float(control["pick_rate"])
        control_picks = int(control["picks"])
        control_reps = int(control["reps"])

        for _, row in model_df.iterrows():
            arm = str(row["arm"])
            if arm == "control":
                continue
            lift = float(row["pick_rate"]) - control_rate
            lift_low = wilson_ci(int(row["picks"]), int(row["reps"]))[0] - wilson_ci(
                control_picks, control_reps
            )[1]
            lift_high = wilson_ci(int(row["picks"]), int(row["reps"]))[1] - wilson_ci(
                control_picks, control_reps
            )[0]
            rows.append(
                {
                    "model": model,
                    "arm": arm,
                    "pick_rate": float(row["pick_rate"]),
                    "control_rate": control_rate,
                    "lift": lift,
                    "lift_ci_low": lift_low,
                    "lift_ci_high": lift_high,
                    "picks": int(row["picks"]),
                    "reps": int(row["reps"]),
                }
            )

    return pd.DataFrame(rows)


def analyze_results(
    config: ExperimentConfig,
    results_dir: str | Path | None = None,
) -> dict[str, pd.DataFrame]:
    """Run full analysis pipeline and write summary tables + charts."""
    out_dir = Path(results_dir or config.results_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_runs(out_dir)
    summary = compute_pick_rates(df)
    lift_df = compute_lift(summary)

    summary.to_csv(out_dir / "pick_rates.csv", index=False)
    lift_df.to_csv(out_dir / "lift_vs_control.csv", index=False)

    _write_summary_markdown(out_dir, summary, lift_df)
    _plot_pick_rates(out_dir, summary)
    _plot_lift(out_dir, lift_df)

    return {"runs": df, "pick_rates": summary, "lift": lift_df}


def _df_to_md_table(df: pd.DataFrame) -> str:
    """Render a DataFrame as a simple markdown table without extra deps."""
    cols = list(df.columns)
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    rows = [
        "| " + " | ".join(str(row[col]) for col in cols) + " |"
        for _, row in df.iterrows()
    ]
    return "\n".join([header, sep, *rows])


def _write_summary_markdown(
    out_dir: Path,
    summary: pd.DataFrame,
    lift_df: pd.DataFrame,
) -> None:
    """Write human-readable analysis summary."""
    lines = ["# Experiment Analysis Summary", ""]
    lines.append("## Pick rates by model and arm")
    lines.append("")
    lines.append(_df_to_md_table(summary.round(3)))
    lines.append("")
    if not lift_df.empty:
        lines.append("## Lift vs control")
        lines.append("")
        lines.append(_df_to_md_table(lift_df.round(3)))
    (out_dir / "analysis_summary.md").write_text("\n".join(lines), encoding="utf-8")


def _plot_pick_rates(out_dir: Path, summary: pd.DataFrame) -> None:
    """Bar chart of pick rates per model."""
    models = summary["model"].unique()
    for model in models:
        model_df = summary[summary["model"] == model].sort_values("arm")
        fig, ax = plt.subplots(figsize=(8, 4))
        x = np.arange(len(model_df))
        rates = model_df["pick_rate"].values
        err_low = rates - model_df["ci_low"].values
        err_high = model_df["ci_high"].values - rates
        ax.bar(x, rates, yerr=[err_low, err_high], capsize=4, color="#2563eb")
        ax.set_xticks(x)
        ax.set_xticklabels(model_df["arm"], rotation=30, ha="right")
        ax.set_ylim(0, 1)
        ax.set_ylabel("Focal pick-rate")
        ax.set_title(f"Pick-rate by treatment arm — {model}")
        fig.tight_layout()
        fig.savefig(out_dir / f"pick_rate_{_safe_model_slug(model)}.png", dpi=150)
        plt.close(fig)

    _plot_pick_rates_combined(out_dir, summary)


def _plot_pick_rates_combined(out_dir: Path, summary: pd.DataFrame) -> None:
    """Combined pick-rate chart across models."""
    arms = sorted(summary["arm"].unique())
    models = summary["model"].unique()
    x = np.arange(len(arms))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    for idx, model in enumerate(models):
        model_df = summary[summary["model"] == model].set_index("arm").reindex(arms)
        offset = (idx - (len(models) - 1) / 2) * width
        ax.bar(x + offset, model_df["pick_rate"], width=width, label=model)

    ax.set_xticks(x)
    ax.set_xticklabels(arms, rotation=30, ha="right")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Focal pick-rate")
    ax.set_title("Pick-rate by arm (all models)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "pick_rate_combined.png", dpi=150)
    plt.close(fig)


def _plot_lift(out_dir: Path, lift_df: pd.DataFrame) -> None:
    """Bar chart of lift vs control per model."""
    if lift_df.empty:
        return

    for model in lift_df["model"].unique():
        model_df = lift_df[lift_df["model"] == model].sort_values("lift", ascending=False)
        fig, ax = plt.subplots(figsize=(8, 4))
        colors = ["#16a34a" if v > 0 else "#dc2626" for v in model_df["lift"]]
        ax.barh(model_df["arm"], model_df["lift"], color=colors)
        ax.axvline(0, color="#666", linewidth=0.8)
        ax.set_xlabel("Lift vs control (pp)")
        ax.set_title(f"Treatment lift — {model}")
        fig.tight_layout()
        fig.savefig(out_dir / f"lift_{_safe_model_slug(model)}.png", dpi=150)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    for model in lift_df["model"].unique():
        model_df = lift_df[lift_df["model"] == model]
        ax.scatter(model_df["arm"], model_df["lift"], label=model, s=80)
    ax.axhline(0, color="#666", linewidth=0.8)
    ax.set_ylabel("Lift vs control (pp)")
    ax.set_title("Lift by arm (all models)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "lift_combined.png", dpi=150)
    plt.close(fig)
