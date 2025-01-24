from enum import StrEnum

class VariantConcordanceEngine(StrEnum):
    """Supported variant concordance analysis engines."""
    HAPPY = "happy"
    WITTYER = "wittyer"