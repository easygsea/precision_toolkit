"""Tests for the summarize_diagnostic_metrics script."""

import subprocess
from pathlib import Path

import pandas as pd
import pytest

from clinical_tools.core.constants import (  # type: ignore
    DEFAULT_DECIMALS,
)
from clinical_tools.core.statistics.proportion import (  # type: ignore
    ProportionConfidenceIntervalMethod,
)


@pytest.fixture
def test_data_dir() -> Path:
    """Fixture for the test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def raw_summary_files(test_data_dir: Path) -> list[Path]:
    """Fixture for raw summary files."""
    return [
        test_data_dir / "sample1.happy.raw.summary.csv",
        test_data_dir / "sample2.happy.raw.summary.csv",
    ]


@pytest.fixture
def curated_summary_files(test_data_dir: Path) -> list[Path]:
    """Fixture for curated summary files."""
    return [
        test_data_dir / "sample1.happy.curated.summary.csv",
        test_data_dir / "sample2.happy.curated.summary.csv",
    ]


def test_summarize_diagnostic_metrics(
    tmp_path: Path, raw_summary_files: list[Path], curated_summary_files: list[Path]
) -> None:
    """Test the summarize_diagnostic_metrics script."""
    output_prefix = tmp_path / "diagnostic_metrics"
    output_csvs = [
        output_prefix.with_name(f"{output_prefix.name}_happy_{prefix}_{metric}.csv")
        for prefix in ["raw", "curated"]
        for metric in ["concordance", "sensitivity", "precision", "f1_score"]
    ]
    output_all_data_csvs = [
        output_prefix.with_name(f"{output_prefix.name}_happy_{prefix}_all_data.csv")
        for prefix in ["raw", "curated"]
    ]
    output_md = output_prefix.with_name(f"{output_prefix.name}_happy_combined.md")
    output_docx = output_prefix.with_name(f"{output_prefix.name}_happy_combined.docx")

    # Run the script
    subprocess.run(
        [
            "summarize-diagnostic-metrics",
            "--engine",
            "happy",
            "--raw-files",
            *[str(f) for f in raw_summary_files],
            "--curated-files",
            *[str(f) for f in curated_summary_files],
            "--prefix",
            str(output_prefix),
            "--tp-method",
            "min",
            "--ci-method",
            ProportionConfidenceIntervalMethod.WILSON.value,
            "--ci-level",
            "0.99",
            "--decimals",
            str(DEFAULT_DECIMALS),
            "--include-all-data-csv",
            "true",
        ],
        check=True,
    )

    # Check that output files were created
    for output_csv in output_csvs:
        assert output_csv.exists()
    for output_all_data_csv in output_all_data_csvs:
        assert output_all_data_csv.exists()
    assert output_md.exists()
    assert output_docx.exists()

    # Check the CSV outputs
    for output_csv in output_csvs:
        df = pd.read_csv(output_csv)

        # Check metric-specific columns
        metric = (
            output_csv.stem.split("raw_")[-1]
            .split("curated_")[-1]
            .replace("_", " ")
            .title()
        )
        assert metric in df.columns
