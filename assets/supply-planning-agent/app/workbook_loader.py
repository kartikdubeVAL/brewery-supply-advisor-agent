"""
Loads the Alpenquell Brauerei Excel workbook into typed in-memory structures.

The workbook has three sheets:
  - Demand Uplift:    region, brand, week_start, week_end, extra_demand_hl
  - Packaging Lines:  line_id, brewery, format, free_capacity_hl_per_week
  - Tank Inventory:   tank_id, brewery, region, brand, ready_week,
                      total_volume_hl, allocated_volume_hl, free_volume_hl,
                      qc_status, qc_note
"""

import logging
import os
from dataclasses import dataclass, field

import openpyxl

logger = logging.getLogger(__name__)

DEFAULT_EXCEL_PATH = os.path.join(os.path.dirname(__file__), "data", "brewery_supply_data.xlsx")


@dataclass
class DemandUplift:
    region: str
    brand: str
    week_start: int
    week_end: int
    extra_demand_hl: float


@dataclass
class PackagingLine:
    line_id: str
    brewery: str
    format: str
    free_capacity_hl_per_week: float


@dataclass
class Tank:
    tank_id: str
    brewery: str
    region: str
    brand: str
    ready_week: int
    total_volume_hl: float
    allocated_volume_hl: float
    free_volume_hl: float
    qc_status: str
    qc_note: str


@dataclass
class BreweryData:
    demand_uplifts: list = field(default_factory=list)
    packaging_lines: list = field(default_factory=list)
    tanks: list = field(default_factory=list)


# Module-level singleton — loaded once at startup
_brewery_data: BreweryData | None = None


def _to_float(value) -> float:
    """Convert cell value to float, return 0.0 if None or empty."""
    if value is None or value == "":
        return 0.0
    return float(value)


def _to_int(value) -> int:
    """Convert cell value to int, return 0 if None or empty."""
    if value is None or value == "":
        return 0
    return int(float(value))


def _to_str(value) -> str:
    """Convert cell value to stripped string."""
    if value is None:
        return ""
    return str(value).strip()


def load_workbook(path: str | None = None) -> BreweryData:
    """
    Parse the Excel workbook and return a BreweryData instance.

    Reads from the path provided, or from the BREWERY_EXCEL_PATH environment
    variable, or from the default location at app/data/brewery_supply_data.xlsx.

    Raises:
        ValueError: If a required sheet is missing or the file cannot be read.
    """
    excel_path = path or os.environ.get("BREWERY_EXCEL_PATH", DEFAULT_EXCEL_PATH)

    logger.info("Loading brewery workbook from: %s", excel_path)

    try:
        wb = openpyxl.load_workbook(excel_path, data_only=True)
    except FileNotFoundError:
        raise ValueError(f"Excel workbook not found at: {excel_path}")
    except Exception as exc:
        raise ValueError(f"Failed to open Excel workbook: {exc}") from exc

    required_sheets = {"Demand Uplift", "Packaging Lines", "Tank Inventory"}
    missing = required_sheets - set(wb.sheetnames)
    if missing:
        raise ValueError(f"Missing required sheets: {sorted(missing)}")

    # --- Parse Demand Uplift ---
    demand_uplifts = []
    ws = wb["Demand Uplift"]
    rows = list(ws.iter_rows(values_only=True))
    for row in rows[1:]:  # skip header
        if row[0] is None:
            continue
        demand_uplifts.append(DemandUplift(
            region=_to_str(row[0]),
            brand=_to_str(row[1]),
            week_start=_to_int(row[2]),
            week_end=_to_int(row[3]),
            extra_demand_hl=_to_float(row[4]),
        ))

    # --- Parse Packaging Lines ---
    packaging_lines = []
    ws = wb["Packaging Lines"]
    rows = list(ws.iter_rows(values_only=True))
    for row in rows[1:]:  # skip header
        if row[0] is None:
            continue
        packaging_lines.append(PackagingLine(
            line_id=_to_str(row[0]),
            brewery=_to_str(row[1]),
            format=_to_str(row[2]),
            free_capacity_hl_per_week=_to_float(row[3]),
        ))

    # --- Parse Tank Inventory ---
    tanks = []
    ws = wb["Tank Inventory"]
    rows = list(ws.iter_rows(values_only=True))
    for row in rows[1:]:  # skip header
        if row[0] is None:
            continue
        tanks.append(Tank(
            tank_id=_to_str(row[0]),
            brewery=_to_str(row[1]),
            region=_to_str(row[2]),
            brand=_to_str(row[3]),
            ready_week=_to_int(row[4]),
            total_volume_hl=_to_float(row[5]),
            allocated_volume_hl=_to_float(row[6]),
            free_volume_hl=_to_float(row[7]),
            qc_status=_to_str(row[8]),
            qc_note=_to_str(row[9]),
        ))

    data = BreweryData(
        demand_uplifts=demand_uplifts,
        packaging_lines=packaging_lines,
        tanks=tanks,
    )
    logger.info(
        "Workbook loaded: %d demand uplifts, %d packaging lines, %d tanks",
        len(data.demand_uplifts),
        len(data.packaging_lines),
        len(data.tanks),
    )
    return data


def get_brewery_data() -> BreweryData:
    """Return the module-level singleton, loading on first call."""
    global _brewery_data
    if _brewery_data is None:
        _brewery_data = load_workbook()
    return _brewery_data


def set_brewery_data(data: BreweryData) -> None:
    """Override the module-level singleton (used in tests)."""
    global _brewery_data
    _brewery_data = data
