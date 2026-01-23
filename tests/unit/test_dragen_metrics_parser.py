"""Tests for parsing metrics derived from DRAGEN output files."""

from pathlib import Path
from typing import Any

import pytest

from clinical_tools.dragen.metrics_parser import DragenMetricsParser  # type: ignore


@pytest.fixture
def test_data_dir(pytestconfig: pytest.Config) -> Path:
    """Fixture for the test data directory."""
    return pytestconfig.rootpath / "tests_data/dragen_metrics"


@pytest.mark.parametrize(
    "metric_name,expected_properties",
    [
        (
            "PCT_CONTAMINATION_EST",
            {
                "mapping_spec": {
                    "Row": ["Estimated sample contamination", 2],
                    "Col": [3],
                },
                "scale_factor": 100.0,
                "scale_factor_op": "multiply",
                "unit": "%",
                "num_decimal_places": 2,
                "fail_threshold": 0.02,
                "fail_direction": "greater_than",
            },
        ),
        (
            "TOTAL_PF_READS",
            {
                "mapping_spec": {"Row": ["Total input reads", 2], "Col": [3]},
                "scale_factor": None,
                "scale_factor_op": "",
                "unit": "Count",
                "num_decimal_places": 0,
                "fail_threshold": None,
                "fail_direction": "",
            },
        ),
        (
            "PCT_CHIMERIC_READS",
            {
                "mapping_spec": {},
                "scale_factor": 100.0,
                "scale_factor_op": "multiply",
                "unit": "%",
                "num_decimal_places": 2,
                "fail_threshold": None,
                "fail_direction": "",
            },
        ),
    ],
    ids=["full_properties", "missing_properties", "derived_metric"],
)
def test_dragen_metric_obj_creation(
    test_data_dir: Path, metric_name: str, expected_properties: dict
) -> None:
    """
    Test DragenMetric objects are created correctly.

    Several scenarios are tested and compared to expected outputs via parametrization:
    - Metric with all properties
    - Metric with missing properties (i.e. factor, failure threshold and direction)
    - Derived metric (i.e. no mapping spec)

    Expected behaviour:
    - DragenMetric object is created and any missing properties are set to "" or None
    """
    json_config_file = test_data_dir / "minimal_config.json"
    dragen_metrics_parser = DragenMetricsParser(
        json_config_file, test_data_dir, "sample"
    )
    metric_obj = dragen_metrics_parser.metric_to_metric_obj[metric_name]

    # Check that DragenMetric object attributes match expected
    for property, expected_val in expected_properties.items():
        assert getattr(metric_obj, property) == expected_val


def test_invalid_config_missing_factor_operation(test_data_dir: Path) -> None:
    """Test that metric with FACTOR but no FactorOperation raises ValueError."""
    json_config_file = test_data_dir / "missing_factor_operation_config.json"
    with pytest.raises(ValueError, match="Factor operation not specified"):
        DragenMetricsParser(json_config_file, test_data_dir, "sample")


@pytest.mark.parametrize(
    "json_config",
    [
        "missing_fail_direction_config.json",
        "missing_fail_threshold_config.json",
    ],
    ids=["missing_direction", "missing_threshold"],
)
def test_invalid_config_incomplete_failure_spec(
    test_data_dir: Path, json_config: str
) -> None:
    """Test metric raises ValueError if only fail threshold or direction is set."""
    json_config_file = test_data_dir / json_config

    with pytest.raises(
        ValueError,
        match="Only one of fail_threshold and fail_direction is specified.",
    ):
        DragenMetricsParser(json_config_file, test_data_dir, "sample")


@pytest.mark.parametrize(
    "sample,expected_metrics",
    [
        (
            "sample",
            {
                "TOTAL_PF_READS": 100,
                "MAPPED_READS": 80.0001,
                "PCT_CONTAMINATION_EST": 0.01,
                "PCT_CHIMERIC_READS_BASE": 20,
                "PCT_CHIMERIC_READS": None,
            },
        ),
        (
            "sample_missing_values",
            {
                "TOTAL_PF_READS": 100,
                "MAPPED_READS": 80.0001,
                "PCT_CONTAMINATION_EST": None,
                "PCT_CHIMERIC_READS_BASE": 20,
                "PCT_CHIMERIC_READS": None,
            },
        ),
        (
            "invalid_sample",
            {
                "TOTAL_PF_READS": None,
                "MAPPED_READS": None,
                "PCT_CONTAMINATION_EST": None,
                "PCT_CHIMERIC_READS_BASE": None,
                "PCT_CHIMERIC_READS": None,
            },
        ),
    ],
    ids=["valid_metrics", "missing_values", "missing_sourcefile"],
)
def test_dragen_metrics_parser(
    test_data_dir: Path, sample: str, expected_metrics: dict[str, Any]
) -> None:
    """
    Test DragenMetricsParser correctly extracts metrics from source files.

    Several scenarios are tested and compared to expected outputs via parametrization:
    - Source files with all values present
    - Source files with missing/None values for specific metrics
    - Missing source files

    Expected behaviour:
    - Metrics with valid values in source files are scaled and returned
    """
    # Create parser and parse metrics
    json_config_file = test_data_dir / "minimal_config.json"
    dragen_metrics_parser = DragenMetricsParser(json_config_file, test_data_dir, sample)
    parsed_metrics = dragen_metrics_parser.parse_metrics()

    # Check that expected metrics are parsed
    parsed_metric_labels = parsed_metrics.keys()
    expected_metric_labels = expected_metrics.keys()
    assert set(expected_metric_labels) == set(parsed_metric_labels)

    # Check that parsed values match expected
    for metric, expected_val in expected_metrics.items():
        parsed_val = parsed_metrics[metric]
        if expected_val is None:
            assert parsed_val is None
        else:
            assert expected_val == pytest.approx(parsed_val)
