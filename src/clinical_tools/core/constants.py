"""Constants for the clinical tools package."""

from enum import StrEnum
from typing import Literal

DiagnosticMetricType = Literal["concordance", "sensitivity", "precision", "f1_score"]


class VariantConcordanceEngine(StrEnum):
    """Supported variant concordance analysis engines."""

    HAPPY = "happy"
    WITTYER = "wittyer"


class NameMapper:
    """Class to hold abbreviations and full names."""

    NAME_MAP = {
        "TP": "True Positive",
        "FP": "False Positive",
        "TN": "True Negative",
        "FN": "False Negative",
    }

    @staticmethod
    def get_full_name(abbreviation: str) -> str:
        """Get the full name of a metric based on its abbreviation."""
        full_name = NameMapper.NAME_MAP.get(abbreviation)
        if full_name is None:
            raise ValueError(f"Unknown abbreviation: {abbreviation}")
        return full_name

    @staticmethod
    def get_abbreviation(full_name: str) -> str:
        """Get the abbreviation of a metric based on its full name."""
        for abbr, name in NameMapper.NAME_MAP.items():
            if name == full_name:
                return abbr
        raise ValueError(f"Unknown full name: {full_name}")
