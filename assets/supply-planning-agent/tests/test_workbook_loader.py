"""Tests for workbook_loader.py"""
import os
import sys
import pytest
import openpyxl

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from workbook_loader import load_workbook, BreweryData, DemandUplift, PackagingLine, Tank


def _create_valid_workbook(tmp_path):
    """Create a minimal valid workbook with all 3 required sheets."""
    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "Demand Uplift"
    ws1.append(["Region", "Brand", "Week Start", "Week End", "Extra Demand (hl)"])
    ws1.append(["South", "Pils", 27, 28, 2400])
    ws1.append(["West", "Pils", 26, 27, 3000])

    ws2 = wb.create_sheet("Packaging Lines")
    ws2.append(["Line ID", "Brewery", "Format", "Free Capacity (hl/week)"])
    ws2.append(["MUC-L01", "Munich", "0.5L bottle", 2000])
    ws2.append(["DOR-L01", "Dortmund", "0.5L bottle", 2500])

    ws3 = wb.create_sheet("Tank Inventory")
    ws3.append(["Tank ID", "Brewery", "Region", "Brand", "Ready Week",
                "Total Volume", "Allocated Volume", "Free Volume", "QC Status", "QC Note"])
    ws3.append(["MUC-T001", "Munich", "South", "Pils", 26, 2000, 800, 1200, "Released", ""])
    ws3.append(["MUC-T002", "Munich", "South", "Pils", 27, 1500, 500, 1000, "Pending", "Lab check"])
    ws3.append(["DOR-T001", "Dortmund", "West", "Pils", 25, 3000, 1200, 1800, "Released", ""])

    path = str(tmp_path / "test.xlsx")
    wb.save(path)
    return path


def test_load_valid_workbook_returns_brewery_data(tmp_path):
    path = _create_valid_workbook(tmp_path)
    data = load_workbook(path)
    assert isinstance(data, BreweryData)
    assert len(data.demand_uplifts) == 2
    assert len(data.packaging_lines) == 2
    assert len(data.tanks) == 3


def test_load_workbook_demand_uplift_fields(tmp_path):
    path = _create_valid_workbook(tmp_path)
    data = load_workbook(path)
    entry = data.demand_uplifts[0]
    assert entry.region == "South"
    assert entry.brand == "Pils"
    assert entry.week_start == 27
    assert entry.week_end == 28
    assert entry.extra_demand_hl == 2400.0


def test_load_workbook_tank_fields(tmp_path):
    path = _create_valid_workbook(tmp_path)
    data = load_workbook(path)
    tank = next(t for t in data.tanks if t.tank_id == "MUC-T001")
    assert tank.brewery == "Munich"
    assert tank.region == "South"
    assert tank.brand == "Pils"
    assert tank.ready_week == 26
    assert tank.total_volume_hl == 2000.0
    assert tank.free_volume_hl == 1200.0
    assert tank.qc_status == "Released"


def test_load_workbook_missing_sheet_raises_value_error(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Demand Uplift"
    ws.append(["Region", "Brand", "Week Start", "Week End", "Extra Demand"])
    # Intentionally missing Packaging Lines and Tank Inventory
    path = str(tmp_path / "incomplete.xlsx")
    wb.save(path)
    with pytest.raises(ValueError, match="Missing required sheets"):
        load_workbook(path)


def test_load_workbook_file_not_found_raises_value_error(tmp_path):
    with pytest.raises(ValueError, match="not found"):
        load_workbook(str(tmp_path / "nonexistent.xlsx"))


def test_load_workbook_packaging_line_fields(tmp_path):
    path = _create_valid_workbook(tmp_path)
    data = load_workbook(path)
    line = next(l for l in data.packaging_lines if l.line_id == "MUC-L01")
    assert line.brewery == "Munich"
    assert line.free_capacity_hl_per_week == 2000.0
