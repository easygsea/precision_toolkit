"""Integration tests for plotting DRAGEN backbone-level metrics."""

import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def test_data_dir(pytestconfig: pytest.Config) -> Path:
    """Fixture for the test data directory."""
    return pytestconfig.rootpath / "tests_data/dragen_metrics"


@pytest.fixture
def modified_metrics_file(test_data_dir: Path, tmp_path: Path) -> Path:
    """Create a copy of PanHeme_MetricsOutput.tsv with IX13680 replaced with IX13681."""
    metrics_file = test_data_dir / "PanHeme_MetricsOutput.tsv"
    modified_metrics_file = tmp_path / "PanHeme_MetricsOutput_modified.tsv"
    modified_metrics_file.write_text(
        metrics_file.read_text().replace("IX13680", "IX13681")
    )
    return modified_metrics_file


EXPECTED_FILES = [
    "TOTAL_PF_READS (Count).png",
    "PCT_CHIMERIC_READS (%).png",
    "PCT_CONTAMINATION_EST (%).png",
    "plot_data.csv",
]


@pytest.mark.parametrize(
    "metrics_file, subfolder",
    [("PanHeme_MetricsOutput.tsv", ""), ("TSO500_MetricsOutput.tsv", "DNA")],
)
def test_plot_dragen_metrics_single(
    test_data_dir: Path, metrics_file: str, subfolder: str
) -> None:
    """Test plot generation given a single MetricsOutput.tsv as input."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_json_config = test_data_dir / "minimal_config.json"
        output_folder = Path(tmpdir) / "plot_dragen_metrics"
        expected_output_folder = (
            output_folder / subfolder if subfolder else output_folder
        )

        subprocess.run(
            [
                "plot-dragen-metrics",
                "--metrics-json-config",
                str(metrics_json_config),
                "--metrics-files",
                str(test_data_dir / metrics_file),
                "--output-folder",
                str(output_folder),
            ],
            check=True,
        )

        for expected_file in EXPECTED_FILES:
            assert (expected_output_folder / expected_file).exists()


def test_plot_dragen_metrics_multiple(
    test_data_dir: Path, modified_metrics_file: Path
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

        for expected_file in EXPECTED_FILES:
            assert (output_folder / expected_file).exists()
