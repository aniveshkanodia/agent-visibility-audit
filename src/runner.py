"""Run experiment reps via LiteLLM."""

from __future__ import annotations

import csv
import json
import random
import time
import uuid
from pathlib import Path

from src.environment import (
    build_prompt,
    load_brand_data,
    load_prompt_template,
    prepare_brand_data,
    prompt_hash,
    randomize_brand_order,
    render_product_cards,
)
from src.schema import AgentChoice, ExperimentConfig, RunRecord, utc_now_iso

MAX_RETRIES = 3
BACKOFF_BASE_SEC = 1.0

GEMINI_3_SYSTEM = (
    "Respond with valid JSON only. Be consistent and factual; base every "
    "recommendation strictly on the product information provided."
)


def run_experiment_matrix(
    config: ExperimentConfig,
    *,
    arms: list[str] | None = None,
    models: list[str] | None = None,
    reps: int | None = None,
    seed: int = 42,
) -> Path:
    """Run all configured conditions and write CSV + JSON logs."""
    results_dir = Path(config.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    brand_data = load_brand_data(config.data_file)
    template = load_prompt_template(config.prompt_template)
    selected_arms = arms or config.arms
    selected_models = models or config.model_ids()
    selected_reps = reps if reps is not None else config.reps

    records: list[RunRecord] = []
    rng = random.Random(seed)

    for model in selected_models:
        litellm_model = config.litellm_for(model)
        for arm in selected_arms:
            for rep in range(1, selected_reps + 1):
                record = run_single_rep(
                    config=config,
                    brand_data=brand_data,
                    template=template,
                    model=model,
                    litellm_model=litellm_model,
                    arm=arm,
                    rep=rep,
                    rng=rng,
                )
                records.append(record)

    csv_path = results_dir / "runs.csv"
    json_path = results_dir / "runs.json"
    _write_csv(csv_path, records)
    _write_json(json_path, records)
    return csv_path


def run_single_rep(
    *,
    config: ExperimentConfig,
    brand_data,
    template: str,
    model: str,
    litellm_model: str,
    arm: str,
    rep: int,
    rng: random.Random,
) -> RunRecord:
    """Execute one experiment repetition."""
    treated = prepare_brand_data(brand_data, arm, overrides=config.treatment_overrides)
    brand_order = randomize_brand_order(
        [config.focal, *config.competitors],
        rng,
    )
    cards = render_product_cards(treated.brands, brand_order)
    prompt = build_prompt(template, cards, config.query)
    phash = prompt_hash(prompt)
    focal_block = treated.brands[config.focal]

    choice = call_agent(prompt, litellm_model)

    focal_picked = _names_match(choice.chosen_brand, focal_block.name)
    return RunRecord(
        run_id=str(uuid.uuid4()),
        timestamp=utc_now_iso(),
        model=model,
        arm=arm,
        rep=rep,
        query=config.query,
        focal_brand_id=config.focal,
        focal_brand_name=focal_block.name,
        brand_order=brand_order,
        prompt_hash=phash,
        prompt=prompt,
        chosen_brand=choice.chosen_brand,
        ranked_list=choice.ranked_list,
        cited_sources=choice.cited_sources,
        confidence=choice.confidence,
        reason=choice.reason,
        focal_picked=focal_picked,
        error=None,
    )


def parse_json_response(content: str) -> dict:
    """Parse model JSON, stripping optional markdown code fences."""
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return json.loads(text)


def _is_gemini_3_or_newer(litellm_model: str) -> bool:
    """Return True for Gemini 3+ models that deprecate temperature/top_p/top_k."""
    return "gemini-3" in litellm_model.lower()


def _completion_kwargs(prompt: str, litellm_model: str) -> dict[str, object]:
    """Build LiteLLM kwargs; Gemini 3+ omits sampling params per provider guidance."""
    messages: list[dict[str, str]] = [{"role": "user", "content": prompt}]
    kwargs: dict[str, object] = {
        "model": litellm_model,
        "messages": messages,
        "response_format": {"type": "json_object"},
    }
    if _is_gemini_3_or_newer(litellm_model):
        messages.insert(0, {"role": "system", "content": GEMINI_3_SYSTEM})
    else:
        kwargs["temperature"] = 0.2
    return kwargs


def call_agent(prompt: str, litellm_model: str) -> AgentChoice:
    """Call LiteLLM with JSON response parsing and retries."""
    from litellm import completion

    last_error: str | None = None
    for attempt in range(MAX_RETRIES):
        try:
            response = completion(**_completion_kwargs(prompt, litellm_model))
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty model response")
            payload = parse_json_response(content)
            return AgentChoice.model_validate(payload)
        except Exception as exc:  # noqa: BLE001 — log and retry all parse/API failures
            last_error = str(exc)
            if attempt < MAX_RETRIES - 1:
                time.sleep(BACKOFF_BASE_SEC * (2**attempt))
            continue

    raise RuntimeError(f"Agent call failed after {MAX_RETRIES} retries: {last_error}")


def _names_match(chosen: str, expected: str) -> bool:
    """Return True if chosen brand name matches expected (fuzzy)."""
    a = chosen.strip().lower()
    b = expected.strip().lower()
    return a == b or a in b or b in a


def _write_csv(path: Path, records: list[RunRecord]) -> None:
    """Write run records to CSV."""
    if not records:
        return
    fieldnames = list(records[0].model_dump().keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            row = record.model_dump()
            row["brand_order"] = json.dumps(row["brand_order"])
            row["ranked_list"] = json.dumps(row["ranked_list"])
            row["cited_sources"] = json.dumps(row["cited_sources"])
            writer.writerow(row)


def _write_json(path: Path, records: list[RunRecord]) -> None:
    """Write run records to JSON."""
    payload = [record.model_dump() for record in records]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
