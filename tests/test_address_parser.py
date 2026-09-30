"""Unit tests for Indian Address Intelligence and Entity Parsing."""

from agents.address_parser import parse_indian_address
from core.schema import AddressQualityTier


def test_parse_high_quality_address():
    raw_addr = "Flat 402, Rosewood Heights, Near HDFC Bank ATM, Koramangala 4th Block, Bengaluru, Karnataka, 560034"
    addr_obj, score = parse_indian_address(raw_addr, "560034")

    assert addr_obj.pincode == "560034"
    assert addr_obj.has_landmark is True
    assert addr_obj.landmark is not None
    assert "HDFC Bank" in addr_obj.landmark or "ATM" in addr_obj.landmark
    assert addr_obj.house_no is not None
    assert score >= 0.70
    assert addr_obj.quality_tier in [AddressQualityTier.HIGH, AddressQualityTier.MEDIUM]


def test_parse_chaotic_address_with_hindi_colloquialism():
    raw_addr = "Shiv Mandir ke pass, lal building, Gali No. 3, Gorakhpur, UP 273001"
    addr_obj, score = parse_indian_address(raw_addr, "273001")

    assert addr_obj.pincode == "273001"
    assert addr_obj.has_landmark is True
    assert "Shiv Mandir" in addr_obj.landmark
    assert score > 0.40


def test_parse_critical_minimal_address():
    raw_addr = "Ward 4, Patna, 800001"
    addr_obj, score = parse_indian_address(raw_addr, "800001")

    assert addr_obj.pincode == "800001"
    assert addr_obj.has_landmark is False
    assert score < 0.60
    assert addr_obj.quality_tier in [AddressQualityTier.LOW, AddressQualityTier.CRITICAL]
