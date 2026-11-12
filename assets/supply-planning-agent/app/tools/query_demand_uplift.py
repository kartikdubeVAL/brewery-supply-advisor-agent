"""Tool: query_demand_uplift — search demand uplift entries by region, brand, and week range."""

import logging
from langchain_core.tools import tool

from workbook_loader import get_brewery_data

logger = logging.getLogger(__name__)


@tool
def query_demand_uplift(region: str, brand: str, week_start: int, week_end: int) -> str:
    """
    Search the Demand Uplift data for entries matching the given region, brand,
    and overlapping week range.

    Args:
        region: Region name (e.g. 'South', 'West', 'East')
        brand: Beer brand (e.g. 'Pils', 'Weizen')
        week_start: Start of the demand week range (calendar week number)
        week_end: End of the demand week range (calendar week number)

    Returns:
        Formatted string listing matching demand uplift entries, or a message
        if no entries were found.
    """
    data = get_brewery_data()
    region_lower = region.strip().lower()
    brand_lower = brand.strip().lower()

    matches = []
    for entry in data.demand_uplifts:
        if entry.region.strip().lower() != region_lower:
            continue
        if entry.brand.strip().lower() != brand_lower:
            continue
        # Check week overlap
        if entry.week_end < week_start or entry.week_start > week_end:
            continue
        matches.append(entry)

    if not matches:
        return (
            f"No demand uplift found for Region='{region}', Brand='{brand}', "
            f"CW{week_start}–CW{week_end} in the loaded data."
        )

    lines = [f"Demand uplift entries for {region} / {brand} overlapping CW{week_start}–CW{week_end}:"]
    total_hl = 0.0
    for m in matches:
        lines.append(
            f"  CW{m.week_start}–CW{m.week_end}: {m.extra_demand_hl:.0f} hl extra demand"
        )
        total_hl += m.extra_demand_hl
    if len(matches) > 1:
        lines.append(f"  Total extra demand: {total_hl:.0f} hl")
    return "\n".join(lines)
