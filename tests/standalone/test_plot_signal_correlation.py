"""Integration tests for signal correlation."""

import subprocess
import tempfile
from pathlib import Path

import pandas as pd
import pytest
from scipy import stats


@pytest.fixture
def test_data_dir():
    """Fixture for the test data directory."""
    return Path(__file__).parent / "data"


def test_plot_signal_correlation_basic(test_data_dir):
    """Generate a plot file without correlation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        truth_signal_file = test_data_dir / "vaf" / "truth" / "sample1_truth_vaf.tsv"
        query_signal_file = test_data_dir / "vaf" / "query" / "sample1_query_vaf.tsv"
        output_figure = Path(tmpdir) / "test_vaf_correlation_basic.png"

        # Run the script
        result = subprocess.run(
            [
                "plot-signal-correlation",
                "--truth-signal",
                str(truth_signal_file),
                "--query-signal",
                str(query_signal_file),
                "--output-figure",
                str(output_figure),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        # Check that the output plot file was created
        assert output_figure.exists(), "Output figure was not created."

        # Verify correlation is not shown in output
        assert "Pearson r = " not in result.stdout, "Unexpected correlation output"
