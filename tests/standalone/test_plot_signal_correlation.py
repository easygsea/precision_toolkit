"""Integration tests for signal correlation."""

import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def test_data_dir() -> Path:
    """Fixture for the test data directory."""
    return Path(__file__).parent / "data"


def test_plot_signal_correlation_basic(test_data_dir: Path) -> None:
    """Generate a plot file without correlation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        truth_signal_file = test_data_dir / "vaf" / "truth" / "sample1_truth_vaf.tsv"
        query_signal_file = test_data_dir / "vaf" / "query" / "sample1_query_vaf.tsv"
        output_filename = Path(tmpdir) / "test_vaf_correlation_basic"

        # Run the script
        subprocess.run(
            [
                "plot-signal-correlation",
                "--truth-signal",
                str(truth_signal_file),
                "--query-signal",
                str(query_signal_file),
                "--output-filename",
                str(output_filename),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        # Check that the output plot file was created
        assert output_filename.with_suffix(".png").exists()
        assert output_filename.with_suffix(".pdf").exists()
        assert output_filename.with_suffix(".tsv").exists()
