"""Tests for tools/list_demand_uplifts.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from workbook_loader import BreweryData, DemandUplift, set_brewery_data
from tools.list_demand_uplifts import list_demand_uplifts


def _setup(demand_uplifts):
    data = BreweryData(demand_uplifts=demand_uplifts, packaging_lines=[], tanks=[])
    set_brewery_data(data)


def test_list_demand_uplifts_shows_entries():
    _setup([
        DemandUplift("South", "Pils", 27, 28, 2400.0),
        DemandUplift("West", "Pils", 26, 27, 3000.0),
    ])
    result = list_demand_uplifts.invoke({})
    assert "South" in result
    assert "West" in result
    assert "2400" in result
    assert "3000" in result


def test_list_demand_uplifts_no_entries():
    _setup([])
    result = list_demand_uplifts.invoke({})
    assert "No demand uplift" in result


def test_list_demand_uplifts_outside_horizon_excluded():
    _setup([
        DemandUplift("South", "Pils", 10, 12, 999.0),  # CW10-12 outside CW25-31
    ])
    result = list_demand_uplifts.invoke({})
    assert "No demand uplift" in result


def test_list_demand_uplifts_shows_total():
    _setup([
        DemandUplift("South", "Pils", 27, 28, 2400.0),
        DemandUplift("West", "Pils", 26, 27, 3000.0),
    ])
    result = list_demand_uplifts.invoke({})
    assert "5400" in result or "Total" in result
