"""Tool: inspect_tank — look up a specific tank by ID and return all its details."""

import logging
from langchain_core.tools import tool

from workbook_loader import get_brewery_data

logger = logging.getLogger(__name__)


@tool
def inspect_tank(tank_id: str) -> str:
    """
    Look up a tank by its ID in the Tank Inventory and return all its fields.

    Args:
        tank_id: The tank identifier (e.g. 'MUC-T001', 'NUE-T006')

    Returns:
        A formatted summary of the tank's fields, or a 'not found' message.
    """
    data = get_brewery_data()
    tank_id_upper = tank_id.strip().upper()

    tank = None
    for t in data.tanks:
        if t.tank_id.strip().upper() == tank_id_upper:
            tank = t
            break

    if tank is None:
        return f"Tank '{tank_id}' not found in the loaded inventory data."

    lines = [f"Tank: {tank.tank_id}"]
    lines.append(f"  Brewery:          {tank.brewery}")
    lines.append(f"  Region:           {tank.region}")
    lines.append(f"  Brand:            {tank.brand}")
    lines.append(f"  Ready Week:       CW{tank.ready_week}")
    lines.append(f"  Total Volume:     {tank.total_volume_hl:.0f} hl")
    lines.append(f"  Allocated Volume: {tank.allocated_volume_hl:.0f} hl (committed to base plan)")
    lines.append(f"  Free Volume:      {tank.free_volume_hl:.0f} hl (available for uplifts)")
    lines.append(f"  QC Status:        {tank.qc_status}")
    if tank.qc_status == "Hold":
        lines.append(f"  QC Note:          {tank.qc_note or 'No note recorded'}")
    elif tank.qc_note:
        lines.append(f"  QC Note:          {tank.qc_note}")

    return "\n".join(lines)
