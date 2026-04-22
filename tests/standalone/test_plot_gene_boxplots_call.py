"""Integration tests for Plot Gene Boxplots Script."""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def test_data_path() -> Path:
    """Provide temporary directory path for testing."""
    return Path(__file__).parent / "data"


def test_plot_gene_boxplots_together(test_data_path: Path) -> None:
    """Test that the plot is generated with all 3 metrics."""
    input_file = test_data_path / "cohort_base_analysis.tsv"

    result = subprocess.run(
        ["plot-gene-boxplots", "--input-file", str(input_file), "--threshold", "15.0"],
        capture_output=True,
        text=True,
        cwd=test_data_path,
    )

    assert result.returncode == 0
    assert result.stderr == ""

    expected_output = test_data_path / "failure_threshold_15.0_boxplot.png"

    assert expected_output.exists()
    assert expected_output.stat().st_size > 1000

    with open(expected_output, "rb") as f:
        assert f.read(8).startswith(b"\x89PNG")

    expected_output.unlink()


def test_plot_gene_boxplots_separate(test_data_path: Path) -> None:
    """Test that the 3 metric plots are generated."""
    input_file = test_data_path / "cohort_base_analysis.tsv"

    result = subprocess.run(
        [
            "plot-gene-boxplots",
            "--input-file",
            str(input_file),
            "--threshold",
            "15.0",
            "--separate-plots",
        ],
        capture_output=True,
        text=True,
        cwd=test_data_path,
    )

    assert result.returncode == 0
    assert result.stderr == ""

    metrics = ["base_quality", "coverage", "mapping_quality"]
    expected_files = [
        test_data_path / f"failure_threshold_15.0_boxplot_{m}.png" for m in metrics
    ]

    for plot_file in expected_files:
        assert plot_file.exists(), f"Expected file {plot_file.name} was not created"
        assert plot_file.stat().st_size > 1000

        with open(plot_file, "rb") as f:
            header = f.read(4)
            assert header == b"\x89PNG", f"{plot_file.name} is not a valid PNG"


def test_plot_gene_boxplots_missing_file() -> None:
    """Test that a missing file has a non-zero return code (failed)."""
    result = subprocess.run(
        [
            "plot-gene-boxplots",
            "--input-file",
            "missing.txt",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0


@pytest.mark.parametrize(
    "threshold, should_pass",
    [
        (0, False),
        (1, True),
        (5, True),
        (10, True),
        (20, True),
        (100, True),
        (1000, False),
    ],
)
def test_plot_gene_boxplots_thresholds(
    test_data_path: Path, threshold: float, should_pass: bool
) -> None:
    """Test that the CLI accepts valid thresholds and rejects invalid ones."""
    input_file = test_data_path / "cohort_base_analysis.tsv"

    result = subprocess.run(
        [
            "plot-gene-boxplots",
            "--input-file",
            str(input_file),
            "--threshold",
            str(threshold),
        ],
        capture_output=True,
        text=True,
        cwd=test_data_path,
    )

    if should_pass:
        return_message = f"CLI failed with threshold {threshold}: {result.stderr}"
        assert result.returncode == 0, return_message

    else:
        assert result.returncode != 0
        assert "Threshold must be between 1 and 100" in result.stderr
