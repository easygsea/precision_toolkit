"""Variant metrics classes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum

from clinical_tools.core.constants import DEFAULT_CI_LEVEL
from clinical_tools.core.statistics.proportion import (
    ProportionConfidenceInterval,
    ProportionConfidenceIntervalMethod,
)


class ConcordanceTPMethod(StrEnum):
    """TP selection methods for variant concordance."""

    TruthTP = "truth"  # Use truth TP for variant concordance
    QueryTP = "query"  # Use query TP for variant concordance
    MinTP = "min"  # Use minimum of truth and query TP for variant concordance


@dataclass(frozen=True)
class VariantCallMetrics:
    """Variant call metrics values.

    Attributes:
        VariantType: Type of variant (e.g., SNV, INDEL)
        VariantCallFilter: Filter status (e.g., PASS, ALL)
        TruthTotal: Total variants in truth set
        TruthTP: True positives in truth set
        TruthFN: False negatives
        QueryTotal: Total variants in query set
        QueryTP: True positives in query set
        QueryFP: False positives
    """

    VariantType: str
    VariantCallFilter: str
    TruthTotal: int
    TruthTP: int
    TruthFN: int
    QueryTotal: int
    QueryTP: int
    QueryFP: int


class BaseVariantCallMetrics(ABC):
    """Abstract base for variant call metrics."""

    def __init__(self, metrics: VariantCallMetrics) -> None:
        """Initialize with metrics data.

        Args:
            metrics: Container with variant metrics data
        """
        self._metrics = metrics

    @property
    def metrics(self) -> VariantCallMetrics:
        """Get the metrics instance."""
        return self._metrics

    @property
    @abstractmethod
    def _ci_successes(self) -> int:
        """Number of successes for confidence interval calculation."""
        pass

    @property
    @abstractmethod
    def _ci_total(self) -> int:
        """Total number for confidence interval calculation."""
        pass

    def confidence_interval(
        self,
        method: ProportionConfidenceIntervalMethod = (
            ProportionConfidenceIntervalMethod.WILSON
        ),
        ci_level: float = DEFAULT_CI_LEVEL,
        **kwargs: dict[str, str],
    ) -> tuple[float, float]:
        """Calculate confidence interval for the metric.

        Args:
            method: Statistical method for CI calculation.
            ci_level: Confidence level for CI calculation.
            **kwargs: Additional parameters for the method.

        Returns:
            Lower and upper bounds of the confidence interval
        """
        return ProportionConfidenceInterval.proportion_confidence_interval(
            successes=self._ci_successes,
            total=self._ci_total,
            method=method,
            ci_level=ci_level,
            **kwargs,
        )


class SensitivityMetrics(BaseVariantCallMetrics):
    """Sensitivity (recall) calculator."""

    @property
    def sensitivity(self) -> float:
        """Calculate the proportion of true positives among all positive calls.

        Returns:
            Sensitivity value between 0 and 1
        """
        if self.metrics.TruthTotal == 0:
            return 0.0
        return self.metrics.TruthTP / self.metrics.TruthTotal

    @property
    def _ci_successes(self) -> int:
        return self.metrics.TruthTP

    @property
    def _ci_total(self) -> int:
        return self.metrics.TruthTotal


class PrecisionMetrics(BaseVariantCallMetrics):
    """Precision calculator."""

    @property
    def precision(self) -> float:
        """Calculate precision.

        Returns:
            Precision value between 0 and 1
        """
        if self.metrics.QueryTotal == 0:
            return 0.0
        return self.metrics.QueryTP / self.metrics.QueryTotal

    @property
    def _ci_successes(self) -> int:
        return self.metrics.QueryTP

    @property
    def _ci_total(self) -> int:
        return self.metrics.QueryTotal


class ConcordanceMetrics(SensitivityMetrics, PrecisionMetrics):
    """Concordance metrics calculator."""

    def __init__(
        self,
        metrics: VariantCallMetrics,
        tp_method: ConcordanceTPMethod,
    ) -> None:
        """Initialize with metrics data and TP selection method.

        Args:
            metrics: Container with variant metrics data
            tp_method: Method for selecting TP in concordance
        """
        super().__init__(metrics)
        self._tp_method = tp_method
        self._tp_selector = {
            ConcordanceTPMethod.TruthTP: self.metrics.TruthTP,
            ConcordanceTPMethod.QueryTP: self.metrics.QueryTP,
            ConcordanceTPMethod.MinTP: min(self.metrics.TruthTP, self.metrics.QueryTP),
        }

    @property
    def _ci_successes(self) -> int:
        return self._tp_selector[self._tp_method]

    @property
    def _ci_total(self) -> int:
        return self._ci_successes + self.metrics.TruthFN + self.metrics.QueryFP

    @property
    def concordance(self) -> float:
        """Calculate concordance rate.

        Returns:
            Concordance value between 0 and 1
        """
        total_calls = self._ci_total
        return 0.0 if total_calls == 0 else self._ci_successes / total_calls


class F1ScoreMetrics:
    """F1 score metric calculator."""

    def __init__(self, precision: float, sensitivity: float) -> None:
        """Initialize with precision and sensitivity values.

        Args:
            precision: Precision value between 0 and 1
            sensitivity: Sensitivity value between 0 and 1
        """
        self.precision = precision
        self.sensitivity = sensitivity

    @property
    def f1_score(self) -> float:
        """Calculate F1 score (harmonic mean of precision and sensitivity).

        Returns:
            F1 score value between 0 and 1
        """
        if self.precision + self.sensitivity == 0:
            return 0.0
        return (
            2 * self.precision * self.sensitivity / (self.precision + self.sensitivity)
        )
