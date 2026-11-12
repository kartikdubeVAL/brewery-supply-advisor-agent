"""
Tool: check_coverage — compute demand coverage for a given uplift event
applying all brewery business rules (QC, regional allocation, packaging capacity).
"""

import logging
from langchain_core.tools import tool

from workbook_loader import get_brewery_data
from business_rules import compute_coverage

logger = logging.getLogger(__name__)


def _format_coverage_answer(result, region: str, brand: str, demand_hl: float,
                             week_start: int, week_end: int) -> str:
    """Format a CoverageResult into the structured answer required by the brewery-coverage-rules skill."""
    lines = []

    # Verdict line
    if result.verdict == "Yes":
        surplus = abs(result.gap_hl)
        lines.append(f"Yes — surplus of {surplus:.0f} hl")
    elif result.verdict == "No":
        lines.append(f"No — gap of {demand_hl:.0f} hl (no secured supply available)")
    else:
        lines.append(f"Partially — gap of {result.gap_hl:.0f} hl "
                     f"(secured {result.secured_hl:.0f} hl of {demand_hl:.0f} hl needed)")

    lines.append("")

    # Secured supply
    lines.append(f"Secured supply ({result.secured_hl:.0f} hl):")
    if result.secured_tanks:
        for t in result.secured_tanks:
            lines.append(f"  - {t['tank_id']} ({t['brewery']}): {t['contributed_hl']:.0f} hl")
    else:
        lines.append("  None")

    lines.append("")

    # Upside (Pending)
    lines.append("Upside (Pending — usable if lab releases in time):")
    if result.upside_tanks:
        for t in result.upside_tanks:
            lines.append(
                f"  - {t['tank_id']} ({t['brewery']}): {t['free_volume_hl']:.0f} hl "
                f"(ready CW{t['ready_week']})"
            )
    else:
        lines.append("  None")

    lines.append("")

    # Hold exclusions
    lines.append("Excluded (Hold):")
    if result.excluded_hold_tanks:
        for t in result.excluded_hold_tanks:
            lines.append(f"  - {t['tank_id']}: {t['qc_note']}")
    else:
        lines.append("  None")

    lines.append("")

    # Packaging lines
    lines.append(f"Packaging lines (CW{week_start}–CW{week_end}, region: {region}):")
    if result.packaging_capacity_hl > 0:
        lines.append(f"  Free capacity: {result.packaging_capacity_hl:.0f} hl total")
        if result.packaging_limited:
            lines.append(
                f"  ⚠ Packaging is the binding constraint "
                f"({result.packaging_capacity_hl:.0f} hl < {result.secured_hl + (result.packaging_capacity_hl - result.secured_hl if result.packaging_limited else 0):.0f} hl tank volume)"
            )
    else:
        lines.append("  No packaging line data available for this region.")

    lines.append("")

    # Recommendation
    lines.append(f"Recommendation: {result.recommendation}")

    return "\n".join(lines)


def _run_coverage_check(region: str, brand: str, demand_hl: float, week_start: int, week_end: int) -> str:
    """
    Plain async helper that runs coverage check with full milestone instrumentation.
    Kept outside the generator so OTel spans work correctly.
    """
    from opentelemetry import trace
    tracer = trace.get_tracer(__name__)
    data = get_brewery_data()

    # M2 – QC rules applied
    with tracer.start_as_current_span("M2-qc-rules-applied"):
        try:
            from business_rules import classify_tank_qc
            region_lower = region.strip().lower()
            brand_lower = brand.strip().lower()
            from business_rules import REGION_BREWERY_MAP
            eligible_breweries = REGION_BREWERY_MAP.get(region_lower, [])
            relevant = [
                t for t in data.tanks
                if t.brewery.strip().lower() in eligible_breweries
                and t.brand.strip().lower() == brand_lower
            ]
            released = sum(1 for t in relevant if classify_tank_qc(t) == "secured")
            pending = sum(1 for t in relevant if classify_tank_qc(t) == "upside")
            hold = sum(1 for t in relevant if classify_tank_qc(t) == "excluded")
            logger.info(
                "M2.achieved: QC classification complete — %d Released, %d Pending, %d Hold",
                released, pending, hold,
            )
        except Exception as exc:
            logger.error("M2.missed: QC classification failed — %s", exc)

    # M3 – Regional allocation validated
    with tracer.start_as_current_span("M3-regional-allocation-validated"):
        try:
            from business_rules import get_eligible_breweries
            brewery_list = get_eligible_breweries(region)
            eligible_tanks = [
                t for t in data.tanks
                if t.brewery.strip().lower() in REGION_BREWERY_MAP.get(region_lower, [])
                and t.brand.strip().lower() == brand_lower
            ]
            logger.info(
                "M3.achieved: Regional filter applied for %s — %d eligible tanks from %s",
                region, len(eligible_tanks), brewery_list,
            )
        except Exception as exc:
            logger.error("M3.missed: Regional allocation check failed — %s", exc)

    # M4 – Packaging line capacity checked
    with tracer.start_as_current_span("M4-packaging-capacity-checked"):
        try:
            from business_rules import REGION_BREWERY_MAP as _RM
            weeks_count = max(1, week_end - week_start + 1)
            cap_hl = sum(
                line.free_capacity_hl_per_week * weeks_count
                for line in data.packaging_lines
                if line.brewery.strip().lower() in _RM.get(region_lower, [])
            )
            from business_rules import get_eligible_breweries as _geb
            brewery_list = _geb(region)
            logger.info(
                "M4.achieved: Packaging capacity checked — effective capacity %.0f hl for %s in CW%d–CW%d",
                cap_hl, brewery_list, week_start, week_end,
            )
        except Exception as exc:
            logger.error("M4.missed: Packaging capacity check failed — %s", exc)

    # Core coverage computation
    try:
        result = compute_coverage(
            demand_hl=demand_hl,
            tanks=data.tanks,
            packaging_lines=data.packaging_lines,
            region=region,
            brand=brand,
            week_start=week_start,
            week_end=week_end,
        )
    except ValueError as exc:
        logger.error("M5.missed: Coverage answer could not be composed — %s", exc)
        return f"Coverage check failed: {exc}"

    # M5 – Coverage answer delivered
    with tracer.start_as_current_span("M5-coverage-answer-delivered"):
        delta_hl = result.gap_hl
        tank_count = len(result.secured_tanks)
        logger.info(
            "M5.achieved: Coverage answer delivered — %s, secured %.0f hl, gap/surplus %.0f hl, %d tanks cited",
            result.verdict, result.secured_hl, delta_hl, tank_count,
        )

    return _format_coverage_answer(result, region, brand, demand_hl, week_start, week_end)


@tool
def check_coverage(region: str, brand: str, demand_hl: float, week_start: int, week_end: int) -> str:
    """
    Compute demand coverage for a given uplift event by applying all brewery
    business rules: QC status, regional brewery allocation, ready-week check,
    free-volume check, and packaging line capacity.

    Args:
        region: Region with the demand uplift (e.g. 'South', 'West', 'East')
        brand: Beer brand (e.g. 'Pils', 'Weizen')
        demand_hl: Extra demand in hectolitres that needs to be covered
        week_start: First calendar week of the uplift period
        week_end: Last calendar week of the uplift period

    Returns:
        Structured coverage answer: verdict, secured tanks, upside tanks,
        Hold exclusions, packaging status, and one recommendation.
    """
    return _run_coverage_check(region, brand, demand_hl, week_start, week_end)
