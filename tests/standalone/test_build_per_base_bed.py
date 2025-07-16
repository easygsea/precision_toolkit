"""Tests for the build_per_base_bed script."""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def test_data_dir():
    """Fixture for the test data directory."""
    return Path(__file__).parent.parent.parent / "tests_data" / "target_evaluation"


@pytest.fixture
def raw_bed_file(test_data_dir):
    """Fixture for input bed file."""
    return test_data_dir / "TSO500_clinical_target_space.bed"


def test_summarize_diagnostic_metrics(tmp_path, raw_bed_file):
    """Test the summarize_build_per_base_bed script."""
    output_prefix = tmp_path / "test_build_per_base_bed"
    output_bed = output_prefix.with_name(f"{raw_bed_file.stem}.per-base.bed")

    # Run the script
    subprocess.run(
        [
            "build_per_base_bed",
            "--input_bed",
            str(raw_bed_file),
            "--output_bed",
            str(output_bed),
        ],
        check=True,
    )

    # Check that output files were created
    assert output_bed.exists()
