"""Concrete treatment-arm edits applied to the focal brand footprint.

Synthetic quotes and statistics below simulate the *form* of third-party corroboration.
We measure whether agents respond to that signal — not whether the claim is factual.
"""

from __future__ import annotations

import copy
import re
from typing import assert_never

from src.schema import BrandBlock, BrandData, TreatmentArm

STATISTIC_INSERT = (
    "Independent lab testing reports 98.7% GPS route accuracy on outdoor runs "
    "and 94% agreement with polysomnography for sleep-stage classification."
)
CITE_SOURCE_INSERT = (
    "Runner's World (2025 buyer's guide): "
    '"The Amazfit Active delivers marathon-grade GPS and multi-day battery at a fraction of flagship prices."'
)
QUOTATION_INSERT = (
    '"For runners who want sleep insights without charging every night, the Amazfit Active is the standout sub-$150 pick." '
    "— TechRadar fitness wearables team, March 2025"
)
PROBLEM_MATCH_PREFIX = (
    "Built for runners who need reliable GPS pace data and detailed overnight sleep staging under $250 — "
)
KEYWORD_STUFF_SUFFIX = (
    " Best smartwatch running sleep tracking under 250 dollars budget fitness watch GPS run sleep tracker "
    "running watch sleep monitor affordable smartwatch sub-250 running sleep combo."
)
CORROBORATE_REVIEW = (
    "GPS and sleep tracking hold up against watches twice the price in our two-week test. — Outdoor Gear Lab"
)
CORROBORATE_EDITORIAL = (
    "Tom's Guide: Amazfit Active earns our budget runner pick for accurate GPS and 14-day battery."
)
COVERAGE_EDITORIAL_2 = (
    "CNET: Strong value for running and sleep tracking if you skip premium smartwatch apps."
)
COVERAGE_EDITORIAL_3 = (
    "Android Authority: Top budget pick for Zepp users who run and track sleep nightly."
)
SIMPLIFY_REPLACEMENT = (
    "Amazfit Active: GPS running watch with sleep tracking. 14-day battery. 5 ATM water resistance. "
    "$129. Works with iPhone and Android."
)
AUTHORITATIVE_SUFFIX = (
    " Industry-leading GPS precision. Unmatched battery endurance. The definitive choice for serious athletes."
)


def apply_treatment(
    data: BrandData,
    arm: TreatmentArm,
    overrides: dict[str, str] | None = None,
) -> BrandData:
    """Apply one treatment edit to the focal brand only; competitors stay fixed.

    Optional ``overrides`` (from config ``treatment_overrides``) replace insert
    strings for arms like ``problem_match`` / ``keyword_stuff`` without changing defaults.
    """
    result = copy.deepcopy(data)
    focal_id = result.focal
    block = result.brands[focal_id]
    arm_override = overrides.get(arm) if overrides else None

    match arm:
        case "control":
            pass
        case "statistic":
            block = _apply_statistic(block)
        case "cite_source":
            block = _apply_cite_source(block)
        case "quotation":
            block = _apply_quotation(block)
        case "problem_match":
            block = _apply_problem_match(block, prefix=arm_override)
        case "keyword_stuff":
            block = _apply_keyword_stuff(block, suffix=arm_override)
        case "corroborate_3x":
            block = _apply_corroborate_3x(block)
        case "coverage_dose":
            block = _apply_coverage_dose(block)
        case "simplify":
            block = _apply_simplify(block)
        case "authoritative":
            block = _apply_authoritative(block)
        case _ as unreachable:
            assert_never(unreachable)

    result.brands[focal_id] = block
    return result


def _apply_statistic(block: BrandBlock) -> BrandBlock:
    """Add a hard-number claim to the brand page."""
    block.brand_page = block.brand_page.rstrip() + " " + STATISTIC_INSERT
    return block


def _apply_cite_source(block: BrandBlock) -> BrandBlock:
    """Add a third-party citation to editorial coverage."""
    block.editorial = list(block.editorial) + [CITE_SOURCE_INSERT]
    return block


def _apply_quotation(block: BrandBlock) -> BrandBlock:
    """Add a credible quote endorsement."""
    block.editorial = list(block.editorial) + [QUOTATION_INSERT]
    return block


def _apply_problem_match(block: BrandBlock, prefix: str | None = None) -> BrandBlock:
    """Explicitly name the query use case in the description."""
    block.brand_page = (prefix or PROBLEM_MATCH_PREFIX) + block.brand_page.lstrip()
    return block


def _apply_keyword_stuff(block: BrandBlock, suffix: str | None = None) -> BrandBlock:
    """Cram query keywords without adding substance (myth-bust arm)."""
    block.brand_page = block.brand_page.rstrip() + (suffix or KEYWORD_STUFF_SUFFIX)
    return block


def _apply_corroborate_3x(block: BrandBlock) -> BrandBlock:
    """Echo the same claim across three independent source types."""
    claim = STATISTIC_INSERT
    block.brand_page = block.brand_page.rstrip() + " " + claim
    block.reviews = list(block.reviews) + [CORROBORATE_REVIEW]
    block.editorial = list(block.editorial) + [CORROBORATE_EDITORIAL]
    return block


def _apply_coverage_dose(block: BrandBlock) -> BrandBlock:
    """Increase source coverage dose with additional editorial mentions."""
    block.editorial = list(block.editorial) + [
        COVERAGE_EDITORIAL_2,
        COVERAGE_EDITORIAL_3,
    ]
    return block


def _apply_simplify(block: BrandBlock) -> BrandBlock:
    """Replace dense copy with plainer, more readable text."""
    block.brand_page = SIMPLIFY_REPLACEMENT
    return block


def _apply_authoritative(block: BrandBlock) -> BrandBlock:
    """Add confident persuasive tone only (myth-bust arm)."""
    block.brand_page = block.brand_page.rstrip() + AUTHORITATIVE_SUFFIX
    return block


def treatment_description(arm: TreatmentArm) -> str:
    """Return a one-line description of the treatment edit."""
    match arm:
        case "control":
            return "No edit — focal footprint as-is."
        case "statistic":
            return "Adds hard-number lab statistics to brand page."
        case "cite_source":
            return "Adds third-party Runner's World citation to editorial."
        case "quotation":
            return "Adds TechRadar quote endorsement to editorial."
        case "problem_match":
            return "Prefixes description with running + sleep + under-$250 framing."
        case "keyword_stuff":
            return "Appends query keyword stuffing to brand page."
        case "corroborate_3x":
            return "Echoes statistic claim across brand page, review, and editorial."
        case "coverage_dose":
            return "Adds two extra editorial mentions for coverage dose."
        case "simplify":
            return "Replaces brand page with plainer readable copy."
        case "authoritative":
            return "Appends confident authoritative tone only."
        case _ as unreachable:
            assert_never(unreachable)


def footprint_has_statistic(text: str) -> bool:
    """Return True if text contains a hard numeric claim."""
    return bool(re.search(r"\d+(?:\.\d+)?%", text))
