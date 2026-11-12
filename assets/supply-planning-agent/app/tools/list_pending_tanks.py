"""Tool: list_pending_tanks — list Pending tanks ranked by coverage potential."""

import logging
from langchain_core.tools import tool

from workbook_loader import get_brewery_data
from business_rules import REGION_BREWERY_MAP, QC_PENDING

logger = logging.getLogger(__name__)


@tool
def list_pending_tanks(region: str, brand: str) -> str:
    """
    List all Pending (QC status = Pending) tanks in the given region and brand,
    ranked by free volume descending (highest coverage potential first).

    This helps supply planners decide which tanks the lab should prioritise
    for release.

    Args:
        region: Region to filter by (e.g. 'South', 'West', 'East')
        brand: Beer brand to filter by (e.g. 'Pils', 'Weizen')

    Returns:
        Ranked list of Pending tanks with their tank_id, brewery, free_volume_hl,
        and ready_week.
    """
    data = get_brewery_data()
    region_key = region.strip().lower()

    if region_key not in REGION_BREWERY_MAP:
        return (
            f"Unknown region '{region}'. Valid regions are: "
            f"{', '.join(REGION_BREWERY_MAP.keys())}."
        )

    eligible_breweries = REGION_BREWERY_MAP[region_key]
    brand_lower = brand.strip().lower()

    pending = []
    for tank in data.tanks:
        if tank.brewery.strip().lower() not in eligible_breweries:
            continue
        if tank.brand.strip().lower() != brand_lower:
            continue
        if tank.qc_status.strip() != QC_PENDING:
            continue
        pending.append(tank)

    if not pending:
        return (
            f"No Pending tanks found for Region='{region}', Brand='{brand}' "
            "in the loaded inventory data."
        )

    # Sort by free_volume_hl descending
    pending.sort(key=lambda t: t.free_volume_hl, reverse=True)

    lines = [
        f"Pending tanks for {region} / {brand} — ranked by coverage potential (highest first):"
    ]
    total_upside = 0.0
    for i, tank in enumerate(pending, 1):
        lines.append(
            f"  {i}. {tank.tank_id} ({tank.brewery}): "
            f"{tank.free_volume_hl:.0f} hl free, ready CW{tank.ready_week}"
        )
        if tank.qc_note:
            lines.append(f"     QC note: {tank.qc_note}")
        total_upside += tank.free_volume_hl

    lines.append(f"\n  Total upside if all released: {total_upside:.0f} hl")
    return "\n".join(lines)
