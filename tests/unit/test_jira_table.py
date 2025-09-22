"""Tests for JIRA table writer."""

import pandas as pd
import pytest
from unittest.mock import mock_open, patch

from clinical_tools.core.writers.jira_table import (
    pandas_to_jira_table,
    populate_jira_table,
    save_jira_table,
    save_dataframe_as_jira_table,
)


class TestPandasToJiraTable:
    """Test pandas_to_jira_table function."""

    def test_basic_dataframe(self):
        """Test basic DataFrame conversion."""
        df = pd.DataFrame({
            'Name': ['Alice', 'Bob'],
            'Age': [25, 30],
            'City': ['NYC', 'LA']
        })
        
        result = pandas_to_jira_table(df)
        
        # Verify JIRA table structure: headers with double pipes, data with single pipes
        assert "||Name||Age||City||" in result
        assert "Alice|25|NYC" in result
        assert "Bob|30|LA" in result
        assert result.count("||") >= 6  # At least 6 double pipes for 3 columns

    def test_empty_dataframe(self):
        """Test empty DataFrame handling."""
        df = pd.DataFrame()
        
        result = pandas_to_jira_table(df)
        expected = "||No data available||"
        
        assert result == expected

    def test_dataframe_with_numeric_values(self):
        """Test DataFrame with numeric values."""
        df = pd.DataFrame({
            'ID': [1, 2, 3],
            'Score': [95.5, 87.2, 92.1]
        })
        
        result = pandas_to_jira_table(df)
        
        # Verify JIRA table structure
        assert "||ID||Score||" in result
        assert "1|95.5" in result
        assert "2|87.2" in result
        assert "3|92.1" in result

    def test_dataframe_with_special_characters(self):
        """Test DataFrame with special characters in column names and values."""
        df = pd.DataFrame({
            'Column Name': ['Value 1', 'Value 2'],
            'Special_Chars': ['Test & More', 'Test < 5']
        })
        
        result = pandas_to_jira_table(df)
        
        # Verify JIRA table structure
        assert "||Column Name||Special_Chars||" in result
        assert "Value 1|Test & More" in result
        assert "Value 2|Test < 5" in result


class TestPopulateJiraTable:
    """Test populate_jira_table function."""

    def test_with_heading_and_summary(self):
        """Test with both heading and summary."""
        df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        
        result = populate_jira_table(df, "Test Table", "This is a summary")
        
        # Verify content structure
        assert "h1. Test Table" in result
        assert "This is a summary" in result
        assert "||A||B||" in result
        assert "1|3" in result
        assert "2|4" in result

    def test_with_heading_only(self):
        """Test with heading only."""
        df = pd.DataFrame({'A': [1], 'B': [2]})
        
        result = populate_jira_table(df, "Test Table")
        
        # Verify content structure
        assert "h1. Test Table" in result
        assert "||A||B||" in result
        assert "1|2" in result

    def test_with_summary_only(self):
        """Test with summary only."""
        df = pd.DataFrame({'A': [1], 'B': [2]})
        
        result = populate_jira_table(df, summary="Test summary")
        
        # Verify content structure
        assert "Test summary" in result
        assert "||A||B||" in result
        assert "1|2" in result

    def test_without_heading_or_summary(self):
        """Test without heading or summary."""
        df = pd.DataFrame({'A': [1], 'B': [2]})
        
        result = populate_jira_table(df)
        
        # Verify content structure
        assert "||A||B||" in result
        assert "1|2" in result


class TestSaveJiraTable:
    """Test save_jira_table function."""

    @patch('builtins.open', new_callable=mock_open)
    def test_save_jira_table_success(self, mock_file):
        """Test successful file save."""
        content = "||A||B||\n1|2"
        output_file = "test.jira"
        
        save_jira_table(content, output_file)
        
        mock_file.assert_called_once_with(output_file, "w")
        mock_file().write.assert_called_once_with(content)

    @patch('builtins.open', side_effect=IOError("Permission denied"))
    def test_save_jira_table_io_error(self, mock_file):
        """Test file save with IO error."""
        content = "test content"
        output_file = "test.jira"
        
        with pytest.raises(IOError, match="Permission denied"):
            save_jira_table(content, output_file)


class TestSaveDataframeAsJiraTable:
    """Test save_dataframe_as_jira_table function."""

    @patch('clinical_tools.core.writers.jira_table.save_jira_table')
    def test_save_dataframe_as_jira_table(self, mock_save):
        """Test complete DataFrame to JIRA table conversion and save."""
        df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        output_file = "test.jira"
        
        save_dataframe_as_jira_table(df, output_file, "Test", "Summary")
        
        # Verify save_jira_table was called with correct content
        mock_save.assert_called_once()
        call_args = mock_save.call_args
        assert call_args[0][1] == output_file
        
        # Verify the content contains expected elements
        content = call_args[0][0]
        assert "h1. Test" in content
        assert "Summary" in content
        assert "||A||B||" in content
        assert "1|3" in content
        assert "2|4" in content


class TestIntegration:
    """Integration tests for the complete workflow."""

    def test_end_to_end_workflow(self):
        """Test complete workflow from DataFrame to JIRA table string."""
        df = pd.DataFrame({
            'Metric': ['Precision', 'Recall', 'F1-Score'],
            'Value': [0.95, 0.87, 0.91]
        })
        
        # Test the complete workflow
        jira_content = populate_jira_table(
            df, 
            heading="Performance Metrics", 
            summary="Summary of model performance"
        )
        
        # Verify all components are present
        assert "h1. Performance Metrics" in jira_content
        assert "Summary of model performance" in jira_content
        assert "||Metric||Value||" in jira_content
        assert "Precision|0.95" in jira_content
        assert "Recall|0.87" in jira_content
        assert "F1-Score|0.91" in jira_content
