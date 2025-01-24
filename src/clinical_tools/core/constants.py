from enum import StrEnum

class VariantConcordanceEngine(StrEnum):
    """Supported variant concordance analysis engines."""
    HAPPY = "happy"
    WITTYER = "wittyer"

class VariantConcordanceMetricMap:
    """Class to hold variant concordance metric mappings and related methods."""
    
    METRIC_MAP = {
        "TP": "True Positives",
        "FP": "False Positives",
        "TN": "True Negatives",
        "FN": "False Negatives",
    }

    @classmethod
    def get_full_name(cls, abbreviation: str) -> str:
        """Get the full name of a metric based on its abbreviation."""
        if abbreviation not in cls.METRIC_MAP:
            raise ValueError(f"Unknown metric abbreviation: {abbreviation}")
        return cls.METRIC_MAP[abbreviation]