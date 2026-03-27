"""Integration tests for parsing DRAGEN output files for backbone-level metrics."""

import subprocess
import tempfile
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def test_data_dir(pytestconfig: pytest.Config) -> Path:
    """Test data directory."""
    return pytestconfig.rootpath / "tests_data/dragen_metrics"


def _parse_script_output(
    metrics_output: Path,
) -> tuple[list[str], dict[str, dict[str, Any]]]:
    """Parse header and metrics from compile-dragen-metrics output."""
    with open(metrics_output, "r") as metrics_tsv:
        colnames = metrics_tsv.readline().strip().split("\t")

        parsed_metrics = {}
        for line in metrics_tsv:
            fields = line.strip().split("\t")
            if len(fields) >= 3:
                metric_name = fields[0]
                category = fields[1]
                value = None if fields[2] == "None" else float(fields[2])
                failure_direction = None if fields[3] == "None" else fields[3]
                threshold = None if fields[4] == "None" else float(fields[4])
                status = None if fields[5] == "None" else fields[5]

            parsed_metrics[metric_name] = {
                "value": value,
                "category": category,
                "threshold": threshold,
                "failure_direction": failure_direction,
                "status": status,
            }

    return colnames, parsed_metrics


@pytest.mark.parametrize(
    "rgsm,expected_metrics",
    [
        (
            "sample",
            {
                "TOTAL_PF_READS (Count)": {
                    "value": 100.0,
                    "category": "Monitoring",
                    "threshold": None,
                    "failure_direction": None,
                    "status": None,
                },
                "PCT_CONTAMINATION_EST (%)": {
                    "value": 0.01,
                    "category": "Production",
                    "threshold": 0.02,
                    "failure_direction": "greater_than",
                    "status": "Pass",
                },
                "PCT_CHIMERIC_READS (%)": {
                    "value": 25.0,
                    "category": "Monitoring",
                    "threshold": None,
                    "failure_direction": None,
                    "status": None,
                },
                "PCT_TARGET_250X (%)": {
                    "value": 86.3,
                    "category": "Monitoring",
                    "threshold": None,
                    "failure_direction": None,
                    "status": None,
                },
            },
        ),
        (
            "sample_missing_values",
            {
                "TOTAL_PF_READS (Count)": {
                    "value": 100.0,
                    "category": "Monitoring",
                    "threshold": None,
                    "failure_direction": None,
                    "status": None,
                },
                "PCT_CONTAMINATION_EST (%)": {
                    "value": None,
                    "category": "Production",
                    "threshold": 0.02,
                    "failure_direction": "greater_than",
                    "status": "Fail",
                },
                "PCT_CHIMERIC_READS (%)": {
                    "value": 25.0,
                    "category": "Monitoring",
                    "threshold": None,
                    "failure_direction": None,
                    "status": None,
                },
                "PCT_TARGET_250X (%)": {
                    "value": None,
                    "category": "Monitoring",
                    "threshold": None,
                    "failure_direction": None,
                    "status": None,
                },
            },
        ),
        (
            "invalid_sample",
            {
                "TOTAL_PF_READS (Count)": {
                    "value": None,
                    "category": "Monitoring",
                    "threshold": None,
                    "failure_direction": None,
                    "status": None,
                },
                "PCT_CONTAMINATION_EST (%)": {
                    "value": None,
                    "category": "Production",
                    "threshold": 0.02,
                    "failure_direction": "greater_than",
                    "status": "Fail",
                },
                "PCT_CHIMERIC_READS (%)": {
                    "value": None,
                    "category": "Monitoring",
                    "threshold": None,
                    "failure_direction": None,
                    "status": None,
                },
                "PCT_TARGET_250X (%)": {
                    "value": None,
                    "category": "Monitoring",
                    "threshold": None,
                    "failure_direction": None,
                    "status": None,
                },
            },
        ),
    ],
    ids=["valid_metrics", "missing_values", "missing_sourcefile"],
)
def test_compile_dragen_metrics(
    test_data_dir: Path, rgsm: str, expected_metrics: dict[str, dict[str, Any]]
) -> None:
    """Test compilation of dragen metrics with various input scenarios."""
    with tempfile.TemporaryDirectory() as tmpdir:
        json_config_file = test_data_dir / "minimal_config.json"
        output_prefix = Path(tmpdir) / "compile_dragen_metrics"

        subprocess.run(
            [
                "compile-dragen-metrics",
                "-j",
                str(json_config_file),
                "-a",
                str(test_data_dir),
                "-r",
                rgsm,
                "-o",
                str(output_prefix),
            ],
            check=True,
        )

        output_file = output_prefix / f"{rgsm}_MetricsOutput.tsv"
        assert output_file.exists()

        # Compare parsed to expected values
        parsed_colnames, parsed_metrics = _parse_script_output(output_file)
        expected_colnames = [
            "Metric (UOM)",
            "Category",
            rgsm,
            "FailureDirection",
            "Threshold",
            "Status",
        ]

        # Ensure parsed values match expected
        assert parsed_colnames == expected_colnames
        assert parsed_metrics == expected_metrics
