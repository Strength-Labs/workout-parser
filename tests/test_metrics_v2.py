"""
Tests for v2.0 metric syntax (@metric for prescriptive, ?metric for informational)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.upload_tool import parse_line_as_metric


def test_prescriptive_metric_with_value():
    """Test @ symbol with numeric value (prescriptive metric)"""
    line = "@calories: 2800 cal daily target"
    result = parse_line_as_metric(line)

    assert result is not None
    assert result['metric_type'] == 'calories'
    assert result['value'] == 2800.0
    assert result['unit'] == 'cal'
    assert 'daily target' in result['notes']
    assert result['is_prescriptive'] == True
    print("✓ Prescriptive metric with value parsed correctly")


def test_prescriptive_metric_simple():
    """Test simple prescriptive metric"""
    line = "@protein: 180 g"
    result = parse_line_as_metric(line)

    assert result is not None
    assert result['metric_type'] == 'protein'
    assert result['value'] == 180.0
    assert result['unit'] == 'g'
    assert result['is_prescriptive'] == True
    print("✓ Simple prescriptive metric parsed correctly")


def test_informational_metric_with_notes():
    """Test ? symbol for informational/tracking metric"""
    line = "?weight: kg morning weight, fasted"
    result = parse_line_as_metric(line)

    assert result is not None
    assert result['metric_type'] == 'weight'
    assert result['value'] is None  # No prescribed value
    assert 'kg morning weight, fasted' in result['notes']
    assert result['is_prescriptive'] == False
    print("✓ Informational metric with notes parsed correctly")


def test_informational_metric_simple():
    """Test simple informational metric"""
    line = "?recovery: 1-10"
    result = parse_line_as_metric(line)

    assert result is not None
    assert result['metric_type'] == 'recovery'
    assert result['value'] is None
    assert '1-10' in result['notes']
    assert result['is_prescriptive'] == False
    print("✓ Simple informational metric parsed correctly")


def test_informational_metric_no_inline_notes():
    """Test informational metric with no inline notes (for indented notes)"""
    line = "?weight: kg"
    result = parse_line_as_metric(line)

    assert result is not None
    assert result['metric_type'] == 'weight'
    assert result['value'] is None
    assert 'kg' in result['notes']
    assert result['is_prescriptive'] == False
    print("✓ Informational metric with unit only parsed correctly")


def test_backwards_compat_at_symbol_no_value():
    """Test backwards compatibility: @ symbol without value = informational"""
    line = "@weight: kg morning weight"
    result = parse_line_as_metric(line)

    assert result is not None
    assert result['metric_type'] == 'weight'
    assert result['value'] is None  # No numeric value
    assert 'kg morning weight' in result['notes']
    assert result['is_prescriptive'] == False  # Treated as informational
    print("✓ Backwards compatibility: @ without value treated as informational")


def test_backwards_compat_at_symbol_empty():
    """Test backwards compatibility: @ symbol with empty value"""
    line = "@weight:"
    result = parse_line_as_metric(line)

    assert result is not None
    assert result['metric_type'] == 'weight'
    assert result['value'] is None
    assert result['is_prescriptive'] == False
    print("✓ Backwards compatibility: @ with empty value parsed correctly")


def test_various_units():
    """Test different unit types"""
    test_cases = [
        ("@sleep: 8 hours", 8.0, 'hours', True),
        ("@body_fat: 15.2%", 15.2, '%', True),
        ("?waist: cm", None, '', False),
        ("@calories: 2400 cal", 2400.0, 'cal', True),
    ]

    for line, expected_value, expected_unit, expected_prescriptive in test_cases:
        result = parse_line_as_metric(line)
        assert result is not None
        assert result['value'] == expected_value
        if expected_unit:
            assert result['unit'] == expected_unit
        assert result['is_prescriptive'] == expected_prescriptive

    print("✓ Various units parsed correctly")


def test_non_metric_lines():
    """Test that non-metric lines return None"""
    non_metrics = [
        "Squat",
        "3x5 @ 405",
        "Workout Date: 2025-10-18",
        "This is just a note",
        "",
    ]

    for line in non_metrics:
        result = parse_line_as_metric(line)
        assert result is None

    print("✓ Non-metric lines correctly return None")


def test_metric_type_normalization():
    """Test that metric types are normalized (lowercase)"""
    lines = [
        "@Weight: 185 lbs",
        "?RECOVERY: 1-10",
        "@Sleep: 8 hours",
    ]

    for line in lines:
        result = parse_line_as_metric(line)
        assert result is not None
        assert result['metric_type'].islower()  # Should be lowercase

    print("✓ Metric types normalized to lowercase")


def test_complex_notes():
    """Test metrics with complex notes"""
    line = "?weight: lbs morning weight, fasted, post-bathroom, same time daily"
    result = parse_line_as_metric(line)

    assert result is not None
    assert 'morning weight' in result['notes']
    assert 'post-bathroom' in result['notes']
    assert 'same time daily' in result['notes']
    print("✓ Complex notes parsed correctly")


def run_all_tests():
    """Run all tests"""
    print("Running Metrics v2.0 Tests...")
    print("=" * 60)

    test_prescriptive_metric_with_value()
    test_prescriptive_metric_simple()
    test_informational_metric_with_notes()
    test_informational_metric_simple()
    test_informational_metric_no_inline_notes()
    test_backwards_compat_at_symbol_no_value()
    test_backwards_compat_at_symbol_empty()
    test_various_units()
    test_non_metric_lines()
    test_metric_type_normalization()
    test_complex_notes()

    print("=" * 60)
    print("✅ All tests passed!")


if __name__ == '__main__':
    run_all_tests()
