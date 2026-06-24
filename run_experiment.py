#!/usr/bin/env python3
"""CLI entry point for the Agent Visibility Audit experiment."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.analyze import analyze_results
from src.audit import run_audit, run_before_after, write_audit_report
from src.environment import load_experiment_config
from src.runner import run_experiment_matrix


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run the Agent Visibility Audit experiment harness.",
    )
    parser.add_argument(
        "--config",
        default="config/experiment.yaml",
        help="Path to experiment config YAML",
    )
    parser.add_argument("--reps", type=int, default=None, help="Reps per cell (overrides config)")
    parser.add_argument(
        "--models",
        nargs="+",
        default=None,
        help="Model ids to run (overrides config)",
    )
    parser.add_argument(
        "--arms",
        nargs="+",
        default=None,
        help="Treatment arms to run (overrides config)",
    )
    parser.add_argument("--analyze", action="store_true", help="Analyze existing results/")
    parser.add_argument("--audit", action="store_true", help="Run Agent Visibility Audit on focal brand")
    parser.add_argument(
        "--before-after",
        action="store_true",
        help="Derive control vs top prescribed fix lift from existing results/",
    )
    parser.add_argument(
        "--before-after-arm",
        default="cite_source",
        help="Treatment arm for before/after demo (default: cite_source)",
    )
    return parser.parse_args(argv)


def require_api_keys() -> None:
    """Exit with a clear error if no LLM provider API key is configured."""
    if os.getenv("ANTHROPIC_API_KEY") or os.getenv("GEMINI_API_KEY"):
        return
    print(
        "Error: no API keys found. Set ANTHROPIC_API_KEY and/or GEMINI_API_KEY in .env.",
        file=sys.stderr,
    )
    sys.exit(1)


def main(argv: list[str] | None = None) -> int:
    """Run experiment, analysis, audit, or before/after demo."""
    load_dotenv(override=True)
    args = parse_args(argv)
    config = load_experiment_config(args.config)

    if args.analyze:
        tables = analyze_results(config)
        print(f"Analysis written to {config.results_dir}/")
        print(tables["pick_rates"].to_string(index=False))
        return 0

    if args.audit:
        report = run_audit(config)
        out_path = write_audit_report(report, config.results_dir)
        print(f"Audit written to {out_path}")
        print(f"Query: {report.query} ({report.regime})")
        for vis in report.visibility:
            print(
                f"  {vis.model}: {vis.pick_rate:.0%} share of voice "
                f"({vis.ci_low:.0%}–{vis.ci_high:.0%})"
            )
        for model, rxs in report.prescriptions.items():
            print(f"  Top fixes ({model}):")
            for rx in rxs:
                print(f"    {rx.rank}. {rx.arm} (lift {rx.lift:+.0%})")
        return 0

    if args.before_after:
        result = run_before_after(
            config,
            arm=args.before_after_arm,
        )
        out_path = Path(config.results_dir) / "before_after.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Before/after ({result['arm']}, {result['regime']}):")
        for model, stats in result["per_model"].items():
            print(
                f"  {model}: {stats['before_pick_rate']:.0%} → "
                f"{stats['after_pick_rate']:.0%} "
                f"({stats['lift_pp']:+.0%} pp)"
            )
        return 0

    require_api_keys()
    csv_path = run_experiment_matrix(
        config,
        arms=args.arms,
        models=args.models,
        reps=args.reps,
    )
    print(f"Runs logged to {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
