"""Integration test for JIRA table conversion."""

import subprocess
from pathlib import Path

import pandas as pd
import pytest

from clinical_tools.core.writers.jira_table import (  # type: ignore[import-not-found]
    populate_jira_table,
)


@pytest.fixture
def sample_files(tmp_path: Path) -> dict[str, Path | pd.DataFrame]:
    """Fixture for sample CSV, TSV, EXCEL and JSON files."""
    df = pd.DataFrame(
        {
            "Name": ["Alice", "Bob", "Charlie", "David"],
            "Age": [25, 30, 28, 33],
            "City": ["Vancouver", "Toronto", "Detroit", "LA"],
        }
    )
    csv_file = tmp_path / "sample.csv"
    tsv_file = tmp_path / "sample.tsv"
    json_file = tmp_path / "sample.json"
    excel_file = tmp_path / "sample.xlsx"

    df.to_csv(csv_file, index=False)
    df.to_csv(tsv_file, sep="\t", index=False)
    df.to_json(json_file, lines=False, orient="records")
    df.to_excel(excel_file, index=False)

    return {
        "csv_file": csv_file,
        "tsv_file": tsv_file,
        "json_file": json_file,
        "excel_file": excel_file,
        "df": df,
    }


@pytest.mark.parametrize(
    "file_format",
    ["csv_file", "tsv_file", "excel_file", "json_file"],
    ids=["csv", "tsv", "excel", "json"],
)
def test_jira_table_formats(sample_files: dict[str, Path], file_format: str) -> None:
    """Test basic jira-table command with all allowed file formats."""
    result = subprocess.run(
        ["jira-table", str(sample_files[file_format])],
        check=True,
        capture_output=True,
        text=True,
    )
    assert (
        result.stdout.strip()
        == populate_jira_table(
            sample_files["df"], None, None, float_format=None
        ).strip()
    )


def test_jira_table_stdin(sample_files: dict[str, Path]) -> None:
    """Test basic jira-table command with stdin."""
    result = subprocess.run(
        f"cat {sample_files['csv_file']} | jira-table",
        shell=True,
        check=True,
        capture_output=True,
        text=True,
    )
    assert (
        result.stdout.strip()
        == populate_jira_table(
            sample_files["df"], None, None, float_format=None
        ).strip()
    )


def test_jira_table_args(sample_files: dict[str, Path]) -> None:
    """Test jira-table command with all the arguments."""
    result = subprocess.run(
        [
            "jira-table",
            str(sample_files["tsv_file"]),
            "-f",
            "tsv",
            "-d",
            "\t",
            "--heading",
            "My Table",
            "--summary",
            "This is a summary",
            "--float-format",
            "2",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert (
        result.stdout.strip()
        == populate_jira_table(
            sample_files["df"], "My Table", "This is a summary", 2
        ).strip()
    )


def test_jira_table_empty() -> None:
    """Test jira-table command with no input."""
    result = subprocess.run(["jira-table"], check=False, capture_output=True, text=True)
    assert "Error" in result.stderr
