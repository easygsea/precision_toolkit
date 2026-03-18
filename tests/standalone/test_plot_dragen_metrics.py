"""Integration tests for plotting DRAGEN backbone-level metrics."""

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def test_data_dir(pytestconfig: pytest.Config) -> Path:
    """Test data directory."""
    return pytestconfig.rootpath / "tests_data/dragen_metrics"


@pytest.fixture
def expected_checksums(test_data_dir: Path) -> dict:
    """Load expected checksums."""
    with open(test_data_dir / "test_plot_dragen_metrics_checksums.json") as f:
        return json.load(f)


@pytest.fixture
def modified_metrics_file(test_data_dir: Path, tmp_path: Path) -> Path:
    """Create a copy of PanHeme_MetricsOutput.tsv with IX13680 replaced with IX13681."""
    metrics_file = test_data_dir / "PanHeme_MetricsOutput.tsv"
    modified_metrics_file = tmp_path / "PanHeme_MetricsOutput_modified.tsv"
    modified_metrics_file.write_text(
        metrics_file.read_text().replace("IX13680", "IX13681")
    )
    return modified_metrics_file


@pytest.mark.parametrize(
    "metrics_file, subfolder, additional_args, checksum_json_key",
    [
        ("PanHeme_MetricsOutput.tsv", "", [], "panheme_default"),
        ("TSO500_MetricsOutput.tsv", "DNA", [], "tso500_default"),
        (
            "TSO500_MetricsOutput.tsv",
            "DNA",
            ["--sort-by", "PCT_TARGET_250X (%)"],
            "tso500_sorted",
        ),
        (
            "TSO500_MetricsOutput.tsv",
            "DNA",
            ["--fastq-list", "fastq_list.csv", "--group-by", "Sex"],
            "tso500_grouped",
        ),
        (
            "TSO500_MetricsOutput.tsv",
            "DNA",
            ["--fastq-list", "fastq_list.csv", "--group-by", "Invalid"],
            "tso500_invalid_group",
        ),
        (
            "TSO500_MetricsOutput.tsv",
            "DNA",
            ["--fastq-list", "fastq_list.csv", "--group-by", "Sex", "--truncate-rgsm"],
            "tso500_grouped_truncated",
        ),
    ],
)
def test_plot_dragen_metrics_single(
    test_data_dir: Path,
    expected_checksums: dict,
    metrics_file: str,
    subfolder: str,
    additional_args: list[str],
    checksum_json_key: str,
) -> None:
    """Test plot generation given a single MetricsOutput.tsv as input."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_json_config = test_data_dir / "minimal_config.json"
        output_folder = Path(tmpdir) / "plot_dragen_metrics"
        expected_output_folder = (
            output_folder / subfolder if subfolder else output_folder
        )

        # If --fastq-list is provided, resolve path to fastq_list.csv
        additional_args_resolved = [
            str(test_data_dir / arg) if arg.endswith(".csv") else arg
            for arg in additional_args
        ]

        subprocess.run(
            [
                "plot-dragen-metrics",
                "--metrics-json-config",
                str(metrics_json_config),
                "--metrics-files",
                str(test_data_dir / metrics_file),
                "--output-folder",
                str(output_folder),
                *additional_args_resolved,
            ],
            check=True,
        )

        # Check that MD5 checksum matches with expected
        for filename, expected_md5 in expected_checksums[checksum_json_key].items():
            generated_md5 = hashlib.md5(
                (expected_output_folder / filename).read_bytes()
            ).hexdigest()
            assert generated_md5 == expected_md5


def test_plot_dragen_metrics_multiple(
    test_data_dir: Path,
    expected_checksums: dict,
    modified_metrics_file: Path,
) -> None:
    """Test plot generation given multiple MetricsOutput.tsv files as input."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_json_config = test_data_dir / "minimal_config.json"
        output_folder = Path(tmpdir) / "plot_dragen_metrics"

        subprocess.run(
            [
                "plot-dragen-metrics",
                "--metrics-json-config",
                str(metrics_json_config),
                "--metrics-files",
                str(test_data_dir / "PanHeme_MetricsOutput.tsv"),
                str(modified_metrics_file),
                "--output-folder",
                str(output_folder),
            ],
            check=True,
        )

        # Check that MD5 checksum matches with expected
        for filename, expected_md5 in expected_checksums[
            "panheme_multiple_default"
        ].items():
            generated_md5 = hashlib.md5(
                (output_folder / filename).read_bytes()
            ).hexdigest()
            assert generated_md5 == expected_md5


def test_plot_dragen_metrics_group_by_without_fastq_list(test_data_dir: Path) -> None:
    """Test that group-by without fastq-list exits."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_json_config = test_data_dir / "minimal_config.json"
        output_folder = Path(tmpdir) / "plot_dragen_metrics"

        result = subprocess.run(
            [
                "plot-dragen-metrics",
                "--metrics-json-config",
                str(metrics_json_config),
                "--metrics-files",
                str(test_data_dir / "PanHeme_MetricsOutput.tsv"),
                "--output-folder",
                str(output_folder),
                "--group-by",
                "Sex",
            ],
        )
        assert result.returncode != 0
