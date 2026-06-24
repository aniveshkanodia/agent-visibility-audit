"""Pydantic models for agent output and experiment run records."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

TreatmentArm = Literal[
    "control",
    "statistic",
    "cite_source",
    "quotation",
    "problem_match",
    "keyword_stuff",
    "corroborate_3x",
    "coverage_dose",
    "simplify",
    "authoritative",
]


class AgentChoice(BaseModel):
    """Structured agent recommendation response."""

    chosen_brand: str
    ranked_list: list[str] = Field(default_factory=list)
    cited_sources: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


class BrandBlock(BaseModel):
    """One brand's web footprint blocks."""

    name: str
    price: float
    brand_page: str
    reviews: list[str] = Field(default_factory=list)
    editorial: list[str] = Field(default_factory=list)
    specs: dict[str, bool | int | float | str] = Field(default_factory=dict)


class BrandData(BaseModel):
    """Full smartwatch dataset."""

    focal: str
    brands: dict[str, BrandBlock]


class RunRecord(BaseModel):
    """One experiment rep logged to disk."""

    run_id: str
    timestamp: str
    model: str
    arm: str
    rep: int
    query: str
    focal_brand_id: str
    focal_brand_name: str
    brand_order: list[str]
    prompt_hash: str
    prompt: str
    chosen_brand: str
    ranked_list: list[str]
    cited_sources: list[str]
    confidence: float
    reason: str
    focal_picked: bool
    error: str | None = None


class ExperimentConfig(BaseModel):
    """Parsed experiment.yaml."""

    focal: str
    query: str
    competitors: list[str]
    models: list[dict[str, str]]
    arms: list[str]
    reps: int
    data_file: str
    prompt_template: str
    results_dir: str
    treatment_overrides: dict[str, str] | None = None

    def model_ids(self) -> list[str]:
        """Return short config model ids for logging and CLI."""
        return [m["id"] for m in self.models]

    def litellm_for(self, model_id: str) -> str:
        """Resolve config model entry to LiteLLM model string."""
        for m in self.models:
            if m["id"] == model_id or m["litellm_model"] == model_id:
                return m["litellm_model"]
        return model_id


def utc_now_iso() -> str:
    """Return current UTC timestamp as ISO string."""
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
