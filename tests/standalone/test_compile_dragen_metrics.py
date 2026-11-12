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


def _parse_tsv_output(
    metrics_output: Path,
) -> tuple[list[str], dict[str, dict[str, Any]]]:
    """Parse header and metrics from compile-dragen-metrics output."""
    with open(metrics_output) as metrics_tsv:
        colnames = metrics_tsv.readline().strip().split("\t")

        parsed_metrics = {}
        for line in metrics_tsv:
            fields = line.strip().split("\t")
            if len(fields) >= 3:
                metric_name = fields[0]
                category = fields[1]
                value = None if fields[2] == "NA" else float(fields[2])
                failure_direction = None if fields[3] == "NA" else fields[3]
                threshold = None if fields[4] == "NA" else float(fields[4])
                status = None if fields[5] == "NA" else fields[5]

            parsed_metrics[metric_name] = {
                "value": value,
                "category": category,
                "threshold": threshold,
                "failure_direction": failure_direction,
                "status": status,
            }

    return colnames, parsed_metrics


def _parse_sectioned_tsv_output(
    metrics_output: Path,
) -> tuple[str, list[str], dict[str, dict[str, Any]]]:
    """Parse section header and metrics from sectioned TSV output."""
    with open(metrics_output) as metrics_ini:
        section = metrics_ini.readline().strip()
        colnames = metrics_ini.readline().strip().split("\t")

        parsed_metrics = {}
        for line in metrics_ini:
            fields = line.strip().split("\t")
            metric_name = fields[0]
            lsl = None if fields[1] == "NA" else float(fields[1])
            usl = None if fields[2] == "NA" else float(fields[2])
            value = None if fields[3] == "NA" else float(fields[3])

            parsed_metrics[metric_name] = {
                "lsl": lsl,
                "usl": usl,
                "value": value,
            }

    return section, colnames, parsed_metrics


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

        parsed_colnames, parsed_metrics = _parse_tsv_output(output_file)
        expected_colnames = [
            "Metric (UOM)",
            "Category",
            rgsm,
            "FailureDirection",
            "Threshold",
            "Status",
        ]

        assert parsed_colnames == expected_colnames
        assert parsed_metrics == expected_metrics


@pytest.mark.parametrize(
    "no_failure_threshold_fallback,expected_contamination_usl",
    [(False, 0.02), (True, None)],
    ids=["threshold_fallback", "suppress_threshold_fallback"],
)
def test_compile_dragen_metrics_sectioned_tsv_output(
    test_data_dir: Path,
    no_failure_threshold_fallback: bool,
    expected_contamination_usl: float | None,
) -> None:
    """Test compilation of dragen metrics when ini output is specified."""
    rgsm = "sample"
    section_name = "QC Metrics"
    with tempfile.TemporaryDirectory() as tmpdir:
        json_config_file = test_data_dir / "minimal_config.json"
        output_prefix = Path(tmpdir) / "compile_dragen_metrics"

        command = [
            "compile-dragen-metrics",
            "-j",
            str(json_config_file),
            "-a",
            str(test_data_dir),
            "-r",
            rgsm,
            "-o",
            str(output_prefix),
            "--section-name",
            section_name,
        ]
        if no_failure_threshold_fallback:
            command.append("--no-failure-threshold-fallback")
        subprocess.run(command, check=True)

        output_file = output_prefix / f"{rgsm}_MetricsOutput.tsv"
        assert output_file.exists()

        parsed_header, parsed_colnames, parsed_metrics = _parse_sectioned_tsv_output(
            output_file
        )
        expected_colnames = [
            "Metric (UOM)",
            "LSL Guideline",
            "USL Guideline",
            rgsm,
        ]
        expected_metrics = {
            "TOTAL_PF_READS (Count)": {"lsl": None, "usl": None, "value": 100.0},
            "PCT_CONTAMINATION_EST (%)": {
                "lsl": None,
                "usl": expected_contamination_usl,
                "value": 0.01,
            },
            "PCT_CHIMERIC_READS (%)": {"lsl": None, "usl": 8.0, "value": 25.0},
            "PCT_TARGET_250X (%)": {"lsl": None, "usl": None, "value": 86.3},
        }

        assert parsed_header == f"[{section_name}]"
        assert parsed_colnames == expected_colnames
        assert parsed_metrics == expected_metrics
