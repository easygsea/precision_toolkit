"""Variant metrics classes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from clinical_tools.core.statistics.proportion import (
    ProportionConfidenceInterval,
    ProportionConfidenceIntervalMethod,
)


class ConcordanceTPMethod(Enum):
    """Enum for TP selection methods for variant concordance."""

    TruthTP = "truth"  # Use truth TP for variant concordance
    QueryTP = "query"  # Use query TP for variant concordance
    MinTP = "min"  # Use minimum of truth and query TP for variant concordance (default)


@dataclass(frozen=True)
class VariantCallMetrics:
    """
    Container for variant call metrics data.

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
    """Base class for variant call metrics calculations."""

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

    @abstractmethod
    def confidence_interval(
        self,
        method: ProportionConfidenceIntervalMethod = (
            ProportionConfidenceIntervalMethod.WILSON
        ),
        **kwargs,
    ) -> tuple[float, float]:
        """
        Calculate confidence interval for the metric.

        Args:
            method: Statistical method for CI calculation.
            **kwargs: Additional parameters for the method.

        Returns:
            Lower and upper bounds of the confidence interval
        """
        pass


class SensitivityMetrics(BaseVariantCallMetrics):
    """Handles sensitivity (recall) calculations."""

    @property
    def sensitivity(self) -> float:
        """
        Calculate the proportion of true positives among all positive calls.

        Returns:
            Sensitivity value between 0 and 1
        """
        if self.metrics.TruthTotal == 0:
            return 0.0
        return self.metrics.TruthTP / self.metrics.TruthTotal

    def confidence_interval(
        self,
        method: ProportionConfidenceIntervalMethod = (
            ProportionConfidenceIntervalMethod.WILSON
        ),
        **kwargs,
    ) -> tuple[float, float]:
        """
        Calculate confidence interval for sensitivity.

        Args:
            method: Statistical method for CI calculation.
            **kwargs: Additional parameters for the method.

        Returns:
            Lower and upper bounds of the confidence interval
        """
        return ProportionConfidenceInterval.proportion_confidence_interval(
            successes=self.metrics.TruthTP,
            total=self.metrics.TruthTotal,
            method=method,
            **kwargs,
        )


class PrecisionMetrics(BaseVariantCallMetrics):
    """Handles precision calculations."""

    @property
    def precision(self) -> float:
        """Calculate precision.

        Returns:
            Precision value between 0 and 1
        """
        if self.metrics.QueryTotal == 0:
            return 0.0
        return self.metrics.QueryTP / self.metrics.QueryTotal

    def confidence_interval(
        self,
        method: ProportionConfidenceIntervalMethod = (
            ProportionConfidenceIntervalMethod.WILSON
        ),
        **kwargs,
    ) -> tuple[float, float]:
        """
        Calculate confidence interval for precision.

        Args:
            method: Statistical method for CI calculation.
            **kwargs: Additional parameters for the method.

        Returns:
            Lower and upper bounds of the confidence interval
        """
        return ProportionConfidenceInterval.proportion_confidence_interval(
            successes=self.metrics.QueryTP,
            total=self.metrics.QueryTotal,
            method=method,
            **kwargs,
        )


class ConcordanceMetrics(SensitivityMetrics, PrecisionMetrics):
    """Handles concordance and combined metrics calculations."""

    def __init__(
        self,
        metrics: VariantCallMetrics,
        tp_method: ConcordanceTPMethod = ConcordanceTPMethod.MinTP,
    ) -> None:
        """
        Initialize with metrics data and TP selection method.

        Args:
            metrics: Container with variant metrics data
            tp_method: Method for selecting TP in concordance
        """
        super().__init__(metrics)
        self._tp_method = tp_method

    @property
    def concordance(self) -> float:
        """
        Calculate concordance rate.

        Returns:
            Concordance value between 0 and 1
        """
        selected_tp = {
            ConcordanceTPMethod.TruthTP: self.metrics.TruthTP,
            ConcordanceTPMethod.QueryTP: self.metrics.QueryTP,
        }.get(self._tp_method, min(self.metrics.TruthTP, self.metrics.QueryTP))
        total_calls = selected_tp + self.metrics.TruthFN + self.metrics.QueryFP
        return 0.0 if total_calls == 0 else selected_tp / total_calls

    def confidence_interval(
        self,
        method: ProportionConfidenceIntervalMethod = (
            ProportionConfidenceIntervalMethod.WILSON
        ),
        **kwargs,
    ) -> tuple[float, float]:
        """
        Calculate confidence interval for concordance.

        Args:
            method: Statistical method for CI calculation.
            **kwargs: Additional parameters for the method.

        Returns:
            Lower and upper bounds of the confidence interval
        """
        total_calls = self.metrics.TruthTotal + self.metrics.QueryFP
        return ProportionConfidenceInterval.proportion_confidence_interval(
            successes=self.metrics.TruthTP, total=total_calls, method=method, **kwargs
        )

    @property
    def f1_score(self) -> float:
        """
        Calculate F1 score (harmonic mean of precision and sensitivity).

        Returns:
            F1 score value between 0 and 1
        """
        precision = self.precision
        sensitivity = self.sensitivity
        if precision + sensitivity == 0:
            return 0.0
        return 2 * (precision * sensitivity) / (precision + sensitivity)
