"""Integration tests for manual diagnostic metrics curation."""

import subprocess
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from clinical_tools.core.constants import (  # type: ignore[import-not-found]
    DEFAULT_CI_LEVEL,
    DEFAULT_CI_METHOD,
)


@pytest.fixture
def test_data_dir():
    """Fixture for the test data directory."""
    return Path(__file__).parent / "data"


def test_manual_concordance_curation(test_data_dir):
    """Test manual concordance curation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = test_data_dir / "concordance.csv"
        output_prefix = Path(tmpdir) / "manually_curated_concordance"
        curation = ["SNP:PASS:TP:100", "SNP:PASS:FN:50", "SNP:PASS:FP:20"]

        # Run the script
        subprocess.run(
            [
                "manual-diagnostic-metric-curation",
                "concordance",
                "--input",
                str(input_file),
                "--curation",
                *curation,
                "--output-prefix",
                str(output_prefix),
                "--ci-method",
                DEFAULT_CI_METHOD,
                "--ci-level",
                str(DEFAULT_CI_LEVEL),
            ],
            check=True,
        )

        # Verify the output
        output_csv = output_prefix.with_suffix(".csv")
        assert output_csv.exists()

        df = pd.read_csv(output_csv)
        assert "Concordance" in df.columns
        assert "CI Lower" in df.columns
        assert "CI Upper" in df.columns

        # Verify content
        row = df.iloc[0]
        assert row["Variant Type"] == "SNP"
        assert row["Variant Filter"] == "PASS"
        assert row["True Positive"] == 100
        assert row["False Negative"] == 50
        assert row["False Positive"] == 20
        assert row["Concordance"] == pytest.approx(0.5882, abs=0.0001)
        assert row["CI Lower"] == pytest.approx(0.51309, abs=0.0001)
        assert row["CI Upper"] == pytest.approx(0.65947, abs=0.0001)


def test_manual_sensitivity_curation(test_data_dir):
    """Test manual sensitivity curation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = test_data_dir / "sensitivity.csv"
        output_prefix = Path(tmpdir) / "manually_curated_sensitivity"
        curation = ["SNP:PASS:TP:100", "SNP:PASS:FN:50"]

        # Run the script
        subprocess.run(
            [
                "manual-diagnostic-metric-curation",
                "sensitivity",
                "--input",
                str(input_file),
                "--curation",
                *curation,
                "--output-prefix",
                str(output_prefix),
                "--ci-method",
                DEFAULT_CI_METHOD,
                "--ci-level",
                str(DEFAULT_CI_LEVEL),
            ],
            check=True,
        )

        # Verify the output
        output_csv = output_prefix.with_suffix(".csv")
        assert output_csv.exists()

        df = pd.read_csv(output_csv)
        assert "Sensitivity" in df.columns
        assert "CI Lower" in df.columns
        assert "CI Upper" in df.columns

        # Verify content
        row = df.iloc[0]
        assert row["Variant Type"] == "SNP"
        assert row["Variant Filter"] == "PASS"
        assert row["True Positive"] == 100
        assert row["False Negative"] == 50
        assert row["Sensitivity"] == pytest.approx(0.6666666666666666, abs=0.0001)
        assert row["CI Lower"] == pytest.approx(0.58789, abs=0.0001)
        assert row["CI Upper"] == pytest.approx(0.73711, abs=0.0001)


def test_manual_precision_curation(test_data_dir):
    """Test manual precision curation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = test_data_dir / "precision.csv"
        output_prefix = Path(tmpdir) / "manually_curated_precision"
        curation = ["SNP:PASS:TP:100", "SNP:PASS:FP:50"]

        # Run the script
        subprocess.run(
            [
                "manual-diagnostic-metric-curation",
                "precision",
                "--input",
                str(input_file),
                "--curation",
                *curation,
                "--output-prefix",
                str(output_prefix),
                "--ci-method",
                DEFAULT_CI_METHOD,
                "--ci-level",
                str(DEFAULT_CI_LEVEL),
            ],
            check=True,
        )

        # Verify the output
        output_csv = output_prefix.with_suffix(".csv")
        assert output_csv.exists()

        df = pd.read_csv(output_csv)
        assert "Precision" in df.columns
        assert "CI Lower" in df.columns
        assert "CI Upper" in df.columns

        # Verify content
        row = df.iloc[0]
        assert row["Variant Type"] == "SNP"
        assert row["Variant Filter"] == "PASS"
        assert row["True Positive"] == 100
        assert row["False Positive"] == 50
        assert row["Precision"] == pytest.approx(0.666667, abs=0.0001)
        assert row["CI Lower"] == pytest.approx(0.587897, abs=0.0001)
        assert row["CI Upper"] == pytest.approx(0.737112, abs=0.0001)


def test_manual_f1_score_curation(test_data_dir):
    """Test manual F1 score curation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = test_data_dir / "f1_score.csv"
        output_prefix = Path(tmpdir) / "manually_curated_f1_score"
        curation = ["SNP:PASS:sensitivity:0.95", "SNP:PASS:precision:0.90"]

        # Run the script
        subprocess.run(
            [
                "manual-diagnostic-metric-curation",
                "f1_score",
                "--input",
                str(input_file),
                "--curation",
                *curation,
                "--output-prefix",
                str(output_prefix),
            ],
            check=True,
        )

        # Verify the output
        output_csv = output_prefix.with_suffix(".csv")
        assert output_csv.exists()

        df = pd.read_csv(output_csv)
        assert "F1 Score" in df.columns
        assert "Sensitivity" in df.columns
        assert "Precision" in df.columns

        # Verify content
        row = df.iloc[0]
        assert row["Variant Type"] == "SNP"
        assert row["Variant Filter"] == "PASS"
        assert row["Sensitivity"] == pytest.approx(0.95, abs=0.0001)
        assert row["Precision"] == pytest.approx(0.90, abs=0.0001)
        assert row["F1 Score"] == pytest.approx(0.924324, abs=0.0001)
