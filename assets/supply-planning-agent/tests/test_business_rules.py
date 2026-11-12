"""Tests for business_rules.py"""
import os
import sys
import pytest
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from business_rules import (
    classify_tank_qc,
    get_eligible_breweries,
    is_tank_ready,
    compute_coverage,
)


@dataclass
class FakeTank:
    tank_id: str
    brewery: str
    region: str
    brand: str
    ready_week: int
    total_volume_hl: float
    allocated_volume_hl: float
    free_volume_hl: float
    qc_status: str
    qc_note: str = ""


@dataclass
class FakePackagingLine:
    line_id: str
    brewery: str
    format: str
    free_capacity_hl_per_week: float


def _make_released_tank(tank_id="MUC-T001", brewery="Munich", brand="Pils",
                         ready_week=26, free_volume_hl=1200):
    return FakeTank(
        tank_id=tank_id, brewery=brewery, region="South", brand=brand,
        ready_week=ready_week, total_volume_hl=2000, allocated_volume_hl=800,
        free_volume_hl=free_volume_hl, qc_status="Released",
    )


def _make_packaging_line(brewery="Munich", capacity=2000):
    return FakePackagingLine(line_id="L01", brewery=brewery, format="bottle",
                              free_capacity_hl_per_week=capacity)


# ── classify_tank_qc ───────────────────────────────────────────────────────────

def test_classify_released():
    tank = FakeTank("T1", "Munich", "South", "Pils", 26, 2000, 800, 1200, "Released")
    assert classify_tank_qc(tank) == "secured"


def test_classify_pending():
    tank = FakeTank("T2", "Munich", "South", "Pils", 26, 2000, 800, 1200, "Pending")
    assert classify_tank_qc(tank) == "upside"


def test_classify_hold():
    tank = FakeTank("T3", "Munich", "South", "Pils", 26, 2000, 800, 1200, "Hold", "Diacetyl issue")
    assert classify_tank_qc(tank) == "excluded"


def test_classify_unknown_status_returns_excluded():
    tank = FakeTank("T4", "Munich", "South", "Pils", 26, 2000, 800, 1200, "Unknown")
    assert classify_tank_qc(tank) == "excluded"


# ── get_eligible_breweries ─────────────────────────────────────────────────────

def test_eligible_breweries_south():
    breweries = get_eligible_breweries("South")
    lower = [b.lower() for b in breweries]
    assert "munich" in lower
    assert "nuremberg" in lower


def test_eligible_breweries_west():
    breweries = get_eligible_breweries("West")
    assert any("dortmund" in b.lower() for b in breweries)


def test_eligible_breweries_east():
    breweries = get_eligible_breweries("East")
    assert any("leipzig" in b.lower() for b in breweries)


def test_eligible_breweries_unknown_raises():
    with pytest.raises(ValueError, match="Unknown region"):
        get_eligible_breweries("North")


def test_eligible_breweries_case_insensitive():
    breweries = get_eligible_breweries("south")
    assert len(breweries) == 2


# ── is_tank_ready ──────────────────────────────────────────────────────────────

def test_tank_ready_when_ready_week_before_demand():
    tank = _make_released_tank(ready_week=26)
    assert is_tank_ready(tank, demand_week=27) is True


def test_tank_ready_when_ready_week_equals_demand():
    tank = _make_released_tank(ready_week=27)
    assert is_tank_ready(tank, demand_week=27) is True


def test_tank_not_ready_when_ready_week_after_demand():
    tank = _make_released_tank(ready_week=28)
    assert is_tank_ready(tank, demand_week=27) is False


def test_tank_not_ready_when_free_volume_zero():
    tank = _make_released_tank(ready_week=26, free_volume_hl=0)
    assert is_tank_ready(tank, demand_week=27) is False


# ── compute_coverage ──────────────────────────────────────────────────────────

def test_compute_coverage_yes_when_sufficient():
    tanks = [_make_released_tank(free_volume_hl=1500)]
    lines = [_make_packaging_line(capacity=2000)]
    result = compute_coverage(1000, tanks, lines, "South", "Pils", 27, 28)
    assert result.verdict == "Yes"
    assert result.secured_hl >= 1000
    assert result.gap_hl <= 0


def test_compute_coverage_no_when_no_released_tanks():
    tanks = [FakeTank("T1", "Munich", "South", "Pils", 26, 2000, 800, 1200, "Hold", "Issue")]
    lines = [_make_packaging_line(capacity=2000)]
    result = compute_coverage(1000, tanks, lines, "South", "Pils", 27, 28)
    assert result.verdict == "No"
    assert result.secured_hl == 0
    assert result.gap_hl == 1000


def test_compute_coverage_partially_when_insufficient():
    tanks = [_make_released_tank(free_volume_hl=600)]
    lines = [_make_packaging_line(capacity=2000)]
    result = compute_coverage(1000, tanks, lines, "South", "Pils", 27, 28)
    assert result.verdict == "Partially"
    assert result.secured_hl == 600
    assert result.gap_hl == 400


def test_compute_coverage_hold_tanks_excluded():
    tanks = [
        _make_released_tank("MUC-T001", free_volume_hl=500),
        FakeTank("MUC-T002", "Munich", "South", "Pils", 26, 1000, 200, 800, "Hold", "QC hold reason"),
    ]
    lines = [_make_packaging_line(capacity=2000)]
    result = compute_coverage(300, tanks, lines, "South", "Pils", 27, 28)
    assert any(t["tank_id"] == "MUC-T002" for t in result.excluded_hold_tanks)
    hold = next(t for t in result.excluded_hold_tanks if t["tank_id"] == "MUC-T002")
    assert "QC hold reason" in hold["qc_note"]


def test_compute_coverage_pending_tanks_in_upside():
    tanks = [
        FakeTank("MUC-T003", "Munich", "South", "Pils", 26, 1500, 500, 1000, "Pending", "Lab check"),
    ]
    lines = [_make_packaging_line(capacity=2000)]
    result = compute_coverage(1000, tanks, lines, "South", "Pils", 27, 28)
    assert result.verdict == "No"  # No secured supply
    assert any(t["tank_id"] == "MUC-T003" for t in result.upside_tanks)


def test_compute_coverage_packaging_limits_effective_coverage():
    tanks = [_make_released_tank(free_volume_hl=3000)]
    lines = [_make_packaging_line(capacity=500)]  # Only 500 hl/week × 2 weeks = 1000 hl
    result = compute_coverage(900, tanks, lines, "South", "Pils", 27, 28)
    # Packaging is 500 hl/week × 2 weeks = 1000 hl, which covers 900 hl demand
    assert result.verdict == "Yes"
    assert result.packaging_capacity_hl == 1000.0


def test_compute_coverage_cross_region_tanks_excluded():
    tanks = [
        FakeTank("DOR-T001", "Dortmund", "West", "Pils", 25, 3000, 1200, 1800, "Released", ""),
    ]
    lines = [_make_packaging_line(brewery="Munich", capacity=2000)]
    # Asking for South coverage — Dortmund tank should be excluded
    result = compute_coverage(1000, tanks, lines, "South", "Pils", 27, 28)
    assert result.verdict == "No"
    assert len(result.secured_tanks) == 0


def test_compute_coverage_unknown_region_raises():
    with pytest.raises(ValueError, match="Unknown region"):
        compute_coverage(1000, [], [], "North", "Pils", 27, 28)
