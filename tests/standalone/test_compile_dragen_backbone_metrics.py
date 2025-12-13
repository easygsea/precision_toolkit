"""Integration tests for parsing DRAGEN output files for backbone-level metrics."""

import subprocess
import tempfile
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def test_data_dir() -> Path:
    """Fixture for the test data directory."""
    return Path(__file__).parent / "data"


def _parse_script_output(
    metrics_output: Path,
) -> tuple[list[str], dict[str, dict[str, Any]]]:
    """Parse header and metrics from compile-dragen-backbone-metrics output."""
    with open(metrics_output, "r") as metrics_tsv:
        colnames = metrics_tsv.readline().strip().split("\t")

        parsed_metrics = {}
        for line in metrics_tsv:
            fields = line.strip().split("\t")
            if len(fields) >= 3:
                metric_name = fields[0]
                value = None if fields[1] == "None" else float(fields[1])
                category = fields[2]

            parsed_metrics[metric_name] = {"value": value, "category": category}

    return colnames, parsed_metrics


@pytest.mark.parametrize(
    "sample,expected_metrics",
    [
        (
            "sample",
            {
                "TOTAL_PF_READS (Count)": {"value": 100.0, "category": "Monitoring"},
                "PCT_CONTAMINATION_EST (%)": {"value": 0.2, "category": "Production"},
                "PCT_CHIMERIC_READS (%)": {"value": 25.0, "category": "Monitoring"},
            },
        ),
        (
            "sample_missing_values",
            {
                "TOTAL_PF_READS (Count)": {"value": 100.0, "category": "Monitoring"},
                "PCT_CONTAMINATION_EST (%)": {"value": None, "category": "Monitoring"},
                "PCT_CHIMERIC_READS (%)": {"value": 25.0, "category": "Monitoring"},
            },
        ),
        (
            "invalid_sample",
            {
                "TOTAL_PF_READS (Count)": {"value": None, "category": "Monitoring"},
                "PCT_CONTAMINATION_EST (%)": {"value": None, "category": "Monitoring"},
                "PCT_CHIMERIC_READS (%)": {"value": None, "category": "Monitoring"},
            },
        ),
    ],
    ids=["valid_metrics", "missing_values", "missing_sourcefile"],
)
def test_compile_dragen_metrics(
    test_data_dir: Path, sample: str, expected_metrics: dict[str, dict[str, Any]]
) -> None:
    """Test compilation of dragen metrics with various input scenarios."""
    with tempfile.TemporaryDirectory() as tmpdir:
        json_config_file = test_data_dir / "minimal_dragen_metrics_config.json"
        output_prefix = Path(tmpdir) / "compile_dragen_backbone_metrics"

        subprocess.run(
            [
                "compile-dragen-backbone-metrics",
                "-j",
                str(json_config_file),
                "-a",
                str(test_data_dir),
                "-s",
                sample,
                "-o",
                str(output_prefix),
            ],
            check=True,
        )

        output_file = output_prefix / f"{sample}_MetricsOutput.tsv"
        assert output_file.exists()

        # Compare parsed to expected values
        parsed_colnames, parsed_metrics = _parse_script_output(output_file)
        expected_colnames = ["Metric (UOM)", sample, "Category"]

        # Ensure parsed values match expected
        assert parsed_colnames == expected_colnames
        assert parsed_metrics == expected_metrics
