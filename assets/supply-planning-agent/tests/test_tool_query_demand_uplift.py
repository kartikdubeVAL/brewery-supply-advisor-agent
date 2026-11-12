"""Tests for tools/query_demand_uplift.py"""
import os
import sys
import pytest
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from workbook_loader import BreweryData, DemandUplift, set_brewery_data
from tools.query_demand_uplift import query_demand_uplift


def _setup_data(demand_uplifts):
    data = BreweryData(demand_uplifts=demand_uplifts, packaging_lines=[], tanks=[])
    set_brewery_data(data)


def test_query_demand_uplift_found():
    _setup_data([
        DemandUplift("South", "Pils", 27, 28, 2400.0),
    ])
    result = query_demand_uplift.invoke({"region": "South", "brand": "Pils", "week_start": 27, "week_end": 28})
    assert "2400" in result
    assert "CW27" in result


def test_query_demand_uplift_not_found():
    _setup_data([
        DemandUplift("South", "Pils", 27, 28, 2400.0),
    ])
    result = query_demand_uplift.invoke({"region": "East", "brand": "Pils", "week_start": 27, "week_end": 28})
    assert "No demand uplift found" in result


def test_query_demand_uplift_case_insensitive():
    _setup_data([
        DemandUplift("South", "Pils", 27, 28, 2400.0),
    ])
    result = query_demand_uplift.invoke({"region": "south", "brand": "pils", "week_start": 27, "week_end": 28})
    assert "2400" in result


def test_query_demand_uplift_overlapping_weeks():
    _setup_data([
        DemandUplift("West", "Pils", 26, 27, 3000.0),
    ])
    result = query_demand_uplift.invoke({"region": "West", "brand": "Pils", "week_start": 25, "week_end": 26})
    assert "3000" in result


def test_query_demand_uplift_no_overlap():
    _setup_data([
        DemandUplift("South", "Pils", 27, 28, 2400.0),
    ])
    result = query_demand_uplift.invoke({"region": "South", "brand": "Pils", "week_start": 25, "week_end": 26})
    assert "No demand uplift found" in result
