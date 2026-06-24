"""Load YAML config/data and render numbered product cards for agents."""

from __future__ import annotations

import hashlib
import random
from pathlib import Path

import yaml

from src.schema import BrandBlock, BrandData, ExperimentConfig
from src.treatments import apply_treatment


def load_brand_data(path: str | Path) -> BrandData:
    """Load smartwatches YAML into BrandData."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return BrandData.model_validate(raw)


def load_experiment_config(path: str | Path) -> ExperimentConfig:
    """Load experiment.yaml into ExperimentConfig."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return ExperimentConfig.model_validate(raw)


def load_prompt_template(path: str | Path) -> str:
    """Read prompt template text from disk."""
    return Path(path).read_text(encoding="utf-8")


def prepare_brand_data(
    data: BrandData,
    arm: str,
    overrides: dict[str, str] | None = None,
) -> BrandData:
    """Return brand data with treatment applied to focal brand only."""
    return apply_treatment(data, arm, overrides=overrides)  # type: ignore[arg-type]


def brand_ids_for_run(config: ExperimentConfig) -> list[str]:
    """Return ordered brand ids: focal first, then competitors."""
    return [config.focal, *config.competitors]


def randomize_brand_order(brand_ids: list[str], rng: random.Random) -> list[str]:
    """Shuffle brand card order to reduce position bias."""
    order = list(brand_ids)
    rng.shuffle(order)
    return order


def render_product_cards(
    brands: dict[str, BrandBlock],
    brand_order: list[str],
) -> str:
    """Render numbered product cards for the agent prompt."""
    sections: list[str] = []
    for idx, brand_id in enumerate(brand_order, start=1):
        block = brands[brand_id]
        sections.append(_render_single_card(idx, block))
    return "\n\n".join(sections)


def _render_single_card(index: int, block: BrandBlock) -> str:
    """Render one numbered product card."""
    lines = [
        f"--- Product {index}: {block.name} ---",
        f"Price: ${block.price:.0f}",
        "",
        "Brand page:",
        block.brand_page.strip(),
        "",
        "Customer reviews:",
    ]
    if block.reviews:
        lines.extend(f"- {review}" for review in block.reviews)
    else:
        lines.append("- (none listed)")

    lines.append("")
    lines.append("Editorial / third-party coverage:")
    if block.editorial:
        lines.extend(f"- {item}" for item in block.editorial)
    else:
        lines.append("- (none listed)")

    lines.append("")
    lines.append("Key specs:")
    for key, value in block.specs.items():
        lines.append(f"- {key}: {value}")

    return "\n".join(lines)


def build_prompt(template: str, product_cards: str, query: str) -> str:
    """Fill prompt template placeholders with cards and query."""
    return template.format(product_cards=product_cards, query=query)


def prompt_hash(prompt: str) -> str:
    """Return sha256 hex digest of the full prompt."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]
