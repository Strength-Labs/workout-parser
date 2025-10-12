import textwrap

from upload_tool import (
    build_metric_catalog_index,
    parse_line_as_metric,
    parse_workouts_from_file,
    prepare_assigned_metrics_for_workout,
)


def test_parse_line_as_metric_with_numeric_value():
    metric = parse_line_as_metric("@sleep: 7.5 hours felt great")
    assert metric == {
        "metric_type": "sleep",
        "value": 7.5,
        "unit": "hours",
        "notes": "felt great",
    }


def test_parse_line_as_metric_placeholder():
    metric = parse_line_as_metric("@weight:")
    assert metric == {
        "metric_type": "weight",
        "value": None,
        "unit": "",
        "notes": "",
    }


def test_parse_workouts_from_file_handles_workout_and_nutrition(tmp_path):
    markup = textwrap.dedent(
        """
        Workout Date: 2025-01-01
        Upper Body Day
        @weight: 185.0 lbs feeling ready
        Bench Press
        3x5 @ 185

        Nutrition Date: 2025-01-01
        @calories: 2200 cal
        Meal Pictures
            Upload nightly for the recap
        """
    ).strip()
    file_path = tmp_path / "plan.txt"
    file_path.write_text(markup, encoding="utf-8")
    exercise_map = {
        "bench press": {"id": 1, "type": "resistance"},
        "meal pictures": {"id": 2, "type": "nutrition"},
    }

    assignments = parse_workouts_from_file(str(file_path), user_id=42, exercise_map=exercise_map)

    assert len(assignments) == 2

    workout = assignments[0]
    assert workout["workout_type"] == "default"
    assert workout["title"] == "Upper Body Day"
    assert workout["assigned_exercises"][0]["exercise_id"] == 1
    assert workout["pending_metrics"][0] == {
        "metric_type": "weight",
        "value": 185.0,
        "unit": "lbs",
        "notes": "feeling ready",
        "metric_date": "2025-01-01",
    }

    nutrition = assignments[1]
    assert nutrition["workout_type"] == "nutrition"
    assert nutrition["assigned_exercises"][0]["exercise_id"] == 2
    assert nutrition["pending_metrics"][0]["metric_type"] == "calories"
    assert nutrition["pending_metrics"][0]["value"] == 2200.0


def test_prepare_assigned_metrics_for_workout_maps_catalog():
    metric_catalog = [
        {"id": 10, "name": "Body Weight", "metric_type": "decimal"},
        {"id": 11, "name": "Calories", "metric_type": "integer"},
    ]
    index, slugs = build_metric_catalog_index(metric_catalog)
    assignment = {
        "pending_metrics": [
            {"metric_type": "weight", "value": 185.0, "unit": "lbs", "notes": "", "metric_date": "2025-01-01"},
            {"metric_type": "calories", "value": 2200, "unit": "cal", "notes": "", "metric_date": "2025-01-01"},
        ]
    }

    assigned, skipped = prepare_assigned_metrics_for_workout(assignment, index, slugs)

    assert skipped == []
    assert len(assigned) == 2
    metric_ids = {entry["metric_id"] for entry in assigned}
    assert metric_ids == {10, 11}
    assert "assigned_metrics" in assignment
    assert len(assignment["assigned_metrics"]) == 2
