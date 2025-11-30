"""
Tests for model enums.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from models.enum.bedroom import Bedroom
from models.enum.tariff import Tariff


@pytest.mark.unit
class TestBedroomEnum:
    """Test Bedroom enum."""

    def test_bedroom_values(self):
        """Test all bedroom enum values exist."""
        assert Bedroom.WHITE.value == "white"
        assert Bedroom.GREEN.value == "green"
        assert Bedroom.BOTH.value == "both"
        assert Bedroom.NONE.value == "none"

    def test_bedroom_members(self):
        """Test bedroom enum has expected members."""
        members = [member.name for member in Bedroom]
        assert "WHITE" in members
        assert "GREEN" in members
        assert "BOTH" in members
        assert "NONE" in members
        assert len(members) == 4

    def test_bedroom_by_value(self):
        """Test accessing bedroom by value."""
        assert Bedroom("white") == Bedroom.WHITE
        assert Bedroom("green") == Bedroom.GREEN
        assert Bedroom("both") == Bedroom.BOTH
        assert Bedroom("none") == Bedroom.NONE

    def test_bedroom_invalid_value(self):
        """Test accessing bedroom with invalid value raises error."""
        with pytest.raises(ValueError):
            Bedroom("invalid")


@pytest.mark.unit
class TestTariffEnum:
    """Test Tariff enum."""

    def test_tariff_values(self):
        """Test all tariff enum values exist."""
        assert Tariff.HOURS_12.value == 0
        assert Tariff.DAY.value == 1
        assert Tariff.WORKER.value == 2
        assert Tariff.INCOGNITA_DAY.value == 3
        assert Tariff.INCOGNITA_HOURS.value == 4
        assert Tariff.INCOGNITA_WORKER.value == 5
        assert Tariff.GIFT.value == 6
        assert Tariff.DAY_FOR_COUPLE.value == 7

    def test_tariff_members(self):
        """Test tariff enum has expected members."""
        members = [member.name for member in Tariff]
        assert "HOURS_12" in members
        assert "DAY" in members
        assert "WORKER" in members
        assert "INCOGNITA_DAY" in members
        assert "INCOGNITA_HOURS" in members
        assert "INCOGNITA_WORKER" in members
        assert "GIFT" in members
        assert "DAY_FOR_COUPLE" in members
        assert len(members) == 8

    def test_tariff_by_value(self):
        """Test accessing tariff by value."""
        assert Tariff(0) == Tariff.HOURS_12
        assert Tariff(1) == Tariff.DAY
        assert Tariff(2) == Tariff.WORKER
        assert Tariff(3) == Tariff.INCOGNITA_DAY
        assert Tariff(4) == Tariff.INCOGNITA_HOURS
        assert Tariff(5) == Tariff.INCOGNITA_WORKER
        assert Tariff(6) == Tariff.GIFT
        assert Tariff(7) == Tariff.DAY_FOR_COUPLE

    def test_tariff_invalid_value(self):
        """Test accessing tariff with invalid value raises error."""
        with pytest.raises(ValueError):
            Tariff(999)

    def test_tariff_comparison(self):
        """Test tariff enum comparison."""
        assert Tariff.DAY == Tariff.DAY
        assert Tariff.DAY != Tariff.WORKER
        assert Tariff.DAY.value < Tariff.WORKER.value
