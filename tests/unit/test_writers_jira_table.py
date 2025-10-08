"""Tests for JIRA table writer."""

import pandas as pd
import pytest

from clinical_tools.core.writers.jira_table import (  # type: ignore[import-not-found]
    pandas_to_jira_table,
    populate_jira_table,
)


@pytest.mark.parametrize(
    "table_input",
    [
        {
            "Name": ["Alice", "Bob"],
            "Age": [25, 30],
            "City": ["NYC", "LA"],
        },  # Basic case
        {"A": [1, 2, 3], "B": [10.5, 20.1, 30.6], "C": [100, 200, 300]},  # Numeric case
        {
            "Passed": [True, False, True],
            "Active": [False, False, True],
            "Inactive": [False, False, False],
        },  # Boolean case
        {
            "Product1": ["A|B", "C||D", "東京"],
            "Description": ["Line.Break$", "Pipe | Symbol", "Regular text"],
            "Product_Price": [9.99, "Mango $2", True],
        },  # Special characters case
    ],
    ids=["basic_case", "numeric_values", "boolean_values", "special_characters"],
)
def test_pandas_to_jira_table(table_input: dict[str, list[str | float | bool]]) -> None:
    """Test pandas_to_jira_table function."""
    df = pd.DataFrame(table_input)
    result = pandas_to_jira_table(df)
    for key, values in table_input.items():
        assert key in result
        for value in values:
            assert str(value) in result
    assert result.count("||") >= len(table_input) + 1
    assert result.count("\n") == len(df)


def test_empty_pandas_to_jira_table() -> None:
    """Test empty DataFrame handling."""
    df = pd.DataFrame()
    result = pandas_to_jira_table(df)
    expected = "||No data available||"
    assert result == expected


@pytest.fixture
def basic_df() -> pd.DataFrame:
    """Fixture for a sample dataframe."""
    return pd.DataFrame({"A": [1, 2], "B": [3, 4]})


@pytest.mark.parametrize(
    "heading, summary, expected",
    [
        (
            "This is a heading",
            "This is a summary",
            ["h1. This is a heading", "This is a summary"],
        ),  # heading & summary
        ("This is a heading", None, ["h1. This is a heading", None]),  # heading only
        (None, "This is a summary", [None, "This is a summary"]),  # summary only
        (None, None, [None, None]),  # no heading nor summary
    ],
    ids=["heading_and_summary", "heading_only", "summary_only", "none"],
)
def test_populate_jira_table(
    basic_df: pd.DataFrame,
    heading: str,
    summary: str,
    expected: list[str],
) -> None:
    """Test populate_jira_table function."""
    result = populate_jira_table(basic_df, heading, summary)
    for value in expected:
        if value is not None:
            assert value in result
    assert pandas_to_jira_table(basic_df) in result


def test_empty_populate_jira_table() -> None:
    """Test empty DataFrame handling."""
    empty_df = pd.DataFrame()
    result = populate_jira_table(empty_df, None, None)
    expected = "||No data available||"
    assert result == expected
