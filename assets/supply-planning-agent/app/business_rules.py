"""
Business rules for Alpenquell Brauerei demand coverage assessment.

Rules implemented:
- QC classification: Released → secured, Pending → upside, Hold → excluded
- Regional brewery allocation: South = Munich + Nuremberg, West = Dortmund, East = Leipzig
- Tank eligibility: ready_week ≤ demand_week AND free_volume_hl > 0
- Coverage computation with packaging line capacity check
"""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Region → brewery names (lower-cased for comparison)
REGION_BREWERY_MAP: dict[str, list[str]] = {
    "south": ["munich", "nuremberg"],
    "west": ["dortmund"],
    "east": ["leipzig"],
}

QC_RELEASED = "Released"
QC_PENDING = "Pending"
QC_HOLD = "Hold"


@dataclass
class CoverageResult:
    verdict: str                          # "Yes", "No", "Partially"
    secured_hl: float
    gap_hl: float                         # positive = shortfall, negative = surplus
    secured_tanks: list = field(default_factory=list)    # [{"tank_id": str, "contributed_hl": float}]
    upside_tanks: list = field(default_factory=list)     # [{"tank_id": str, "free_volume_hl": float, "brewery": str}]
    excluded_hold_tanks: list = field(default_factory=list)  # [{"tank_id": str, "qc_note": str}]
    packaging_capacity_hl: float = 0.0
    packaging_limited: bool = False
    recommendation: str = ""


def classify_tank_qc(tank) -> str:
    """
    Classify a tank based on its QC status.

    Returns:
        "secured"  — QC status is Released
        "upside"   — QC status is Pending
        "excluded" — QC status is Hold or unknown
    """
    status = getattr(tank, "qc_status", "") or ""
    status = status.strip()
    if status == QC_RELEASED:
        return "secured"
    if status == QC_PENDING:
        return "upside"
    return "excluded"


def get_eligible_breweries(region: str) -> list[str]:
    """
    Return the list of brewery names (title-cased) for the given region.

    Raises:
        ValueError: if the region is not known.
    """
    key = region.strip().lower()
    if key not in REGION_BREWERY_MAP:
        raise ValueError(
            f"Unknown region '{region}'. Valid regions are: {', '.join(REGION_BREWERY_MAP)}"
        )
    # Return title-cased for display; comparisons use lower
    return [b.title() for b in REGION_BREWERY_MAP[key]]


def is_tank_ready(tank, demand_week: int) -> bool:
    """
    Return True if a tank is ready on or before demand_week and has free volume.
    """
    return (
        getattr(tank, "ready_week", 999) <= demand_week
        and getattr(tank, "free_volume_hl", 0.0) > 0.0
    )


def compute_coverage(
    demand_hl: float,
    tanks: list,
    packaging_lines: list,
    region: str,
    brand: str,
    week_start: int,
    week_end: int,
) -> CoverageResult:
    """
    Apply all business rules to compute demand coverage for a given uplift event.

    Steps:
    1. Filter tanks by region and brand
    2. Classify by QC status
    3. Apply ready-week and free-volume check on secured tanks
    4. Sum free volumes → secured_hl
    5. Check packaging line capacity at matching breweries
    6. Determine verdict and gap/surplus
    """
    region_key = region.strip().lower()
    if region_key not in REGION_BREWERY_MAP:
        raise ValueError(
            f"Unknown region '{region}'. Valid regions are: {', '.join(REGION_BREWERY_MAP)}"
        )
    eligible_brewery_names_lower = REGION_BREWERY_MAP[region_key]
    brand_lower = brand.strip().lower()

    secured_tanks = []
    upside_tanks = []
    excluded_hold_tanks = []

    for tank in tanks:
        tank_brewery_lower = getattr(tank, "brewery", "").strip().lower()
        tank_brand_lower = getattr(tank, "brand", "").strip().lower()

        # Filter: region and brand must match
        if tank_brewery_lower not in eligible_brewery_names_lower:
            continue
        if tank_brand_lower != brand_lower:
            continue

        qc_class = classify_tank_qc(tank)

        if qc_class == "excluded":
            excluded_hold_tanks.append({
                "tank_id": tank.tank_id,
                "qc_note": getattr(tank, "qc_note", "") or "No QC note recorded",
            })
            continue

        if qc_class == "upside":
            upside_tanks.append({
                "tank_id": tank.tank_id,
                "brewery": getattr(tank, "brewery", ""),
                "free_volume_hl": getattr(tank, "free_volume_hl", 0.0),
                "ready_week": getattr(tank, "ready_week", 0),
            })
            continue

        # qc_class == "secured" — check ready week and free volume
        if not is_tank_ready(tank, week_start):
            # Tank not ready by first demand week — skip for secured
            # Still record as upside if ready by week_end
            if is_tank_ready(tank, week_end):
                upside_tanks.append({
                    "tank_id": tank.tank_id,
                    "brewery": getattr(tank, "brewery", ""),
                    "free_volume_hl": getattr(tank, "free_volume_hl", 0.0),
                    "ready_week": getattr(tank, "ready_week", 0),
                })
            continue

        contributed = getattr(tank, "free_volume_hl", 0.0)
        if contributed <= 0:
            continue
        secured_tanks.append({
            "tank_id": tank.tank_id,
            "brewery": getattr(tank, "brewery", ""),
            "contributed_hl": contributed,
        })

    secured_hl = sum(t["contributed_hl"] for t in secured_tanks)

    # --- Packaging line capacity check ---
    packaging_capacity_hl = 0.0
    for line in packaging_lines:
        line_brewery_lower = getattr(line, "brewery", "").strip().lower()
        if line_brewery_lower in eligible_brewery_names_lower:
            # Capacity is per week; multiply by number of demand weeks
            weeks_count = max(1, week_end - week_start + 1)
            packaging_capacity_hl += getattr(line, "free_capacity_hl_per_week", 0.0) * weeks_count

    packaging_limited = packaging_capacity_hl < secured_hl and packaging_capacity_hl > 0
    effective_hl = min(secured_hl, packaging_capacity_hl) if packaging_capacity_hl > 0 else secured_hl

    # --- Verdict ---
    gap_hl = demand_hl - effective_hl
    if effective_hl >= demand_hl:
        verdict = "Yes"
        surplus = effective_hl - demand_hl
        recommendation = (
            f"Coverage confirmed. Deploy secured tanks ({', '.join(t['tank_id'] for t in secured_tanks)}). "
            f"Surplus of {surplus:.0f} hl available as buffer."
        )
        if packaging_limited:
            recommendation += f" Note: packaging capacity ({packaging_capacity_hl:.0f} hl) was the binding constraint."
    elif effective_hl == 0:
        verdict = "No"
        recommendation = (
            "No secured supply available. "
        )
        if upside_tanks:
            recommendation += (
                f"Prioritise lab release of Pending tanks "
                f"({', '.join(t['tank_id'] for t in upside_tanks)}) to create upside."
            )
        else:
            recommendation += "No Pending tanks either — escalate to procurement."
    else:
        verdict = "Partially"
        recommendation = (
            f"Partial coverage: {effective_hl:.0f} hl secured, gap of {gap_hl:.0f} hl. "
        )
        if upside_tanks:
            recommendation += (
                f"Request urgent lab release for Pending tanks "
                f"({', '.join(t['tank_id'] for t in upside_tanks)}) to close the gap."
            )
        else:
            recommendation += "No Pending tanks available to close the gap — consider procurement options."

    if excluded_hold_tanks:
        hold_ids = ", ".join(t["tank_id"] for t in excluded_hold_tanks)
        recommendation += f" Hold tanks excluded: {hold_ids}."

    return CoverageResult(
        verdict=verdict,
        secured_hl=effective_hl,
        gap_hl=gap_hl,
        secured_tanks=secured_tanks,
        upside_tanks=upside_tanks,
        excluded_hold_tanks=excluded_hold_tanks,
        packaging_capacity_hl=packaging_capacity_hl,
        packaging_limited=packaging_limited,
        recommendation=recommendation,
    )
