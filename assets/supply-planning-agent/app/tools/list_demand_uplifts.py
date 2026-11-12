"""Tool: list_demand_uplifts — list all demand uplift entries for the planning horizon."""

import logging
from langchain_core.tools import tool

from workbook_loader import get_brewery_data

logger = logging.getLogger(__name__)

PLANNING_WEEK_START = 25
PLANNING_WEEK_END = 31


@tool
def list_demand_uplifts() -> str:
    """
    List all demand uplift entries for the summer 2027 planning horizon (CW25–CW31).

    Returns a summary table of all demand uplifts: region, brand, weeks,
    and extra demand in hl.
    """
    data = get_brewery_data()

    # Filter to planning horizon
    entries = [
        e for e in data.demand_uplifts
        if not (e.week_end < PLANNING_WEEK_START or e.week_start > PLANNING_WEEK_END)
    ]

    if not entries:
        return (
            f"No demand uplift entries found for the planning horizon "
            f"(CW{PLANNING_WEEK_START}–CW{PLANNING_WEEK_END}) in the loaded data."
        )

    # Sort by region, then brand, then week_start
    entries.sort(key=lambda e: (e.region, e.brand, e.week_start))

    lines = [f"Demand uplifts for summer 2027 planning horizon (CW{PLANNING_WEEK_START}–CW{PLANNING_WEEK_END}):"]
    lines.append(f"  {'Region':<8} {'Brand':<8} {'Weeks':<14} {'Extra Demand (hl)':>18}")
    lines.append("  " + "-" * 52)
    total_hl = 0.0
    for e in entries:
        week_range = f"CW{e.week_start}–CW{e.week_end}"
        lines.append(f"  {e.region:<8} {e.brand:<8} {week_range:<14} {e.extra_demand_hl:>18.0f}")
        total_hl += e.extra_demand_hl
    lines.append("  " + "-" * 52)
    lines.append(f"  {'Total':<22} {total_hl:>18.0f} hl")

    return "\n".join(lines)
