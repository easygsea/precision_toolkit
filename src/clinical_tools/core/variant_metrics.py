from clinical_tools.core.statistics import ProportionConfidenceInterval
from dataclasses import dataclass

@dataclass
class VariantCallMetrics:
  VariantType: str
  VariantCallFilter: str
  TruthTotal: int
  TruthTP: int
  TruthFN: int
  QueryTotal: int
  QueryTP: int
  QueryFP: int


class BaseVariantCallMetrics:
  """
  Base class to hold and process variant call metrics.
  """

  def __init__(self, metrics: VariantCallMetrics):
    """
    Initialize a VariantCallMetrics instance.

    Args:
      metrics (VariantCallMetrics): Metrics object containing variant data.
    """
    self.metrics = metrics


class SensitivityMetrics(BaseVariantCallMetrics):
  """
  Sensitivity-related metrics.
  """

  @property
  def sensitivity(self):
    """
    Calculate and return sensitivity (recall).

    Returns:
      float: Sensitivity (recall).
    """
    if self.metrics.TruthTotal == 0:
      return 0.0
    return self.metrics.TruthTP / self.metrics.TruthTotal

  def confidence_interval(self, method='wilson', **kwargs):
    """
    Calculate the confidence interval for sensitivity.

    Args:
      method (str): Method for confidence interval calculation.
                    Defaults to 'wilson'.
      **kwargs: Additional parameters for the confidence interval method.

    Returns:
      tuple[float, float]: Lower and upper bounds of the confidence interval.
    """
    return ProportionConfidenceInterval.proportion_confidence_interval(
      successes=self.metrics.TruthTP,
      total=self.metrics.TruthTotal,
      method=method,
      **kwargs
    )


class PrecisionMetrics(BaseVariantCallMetrics):
  """
  Precision-related metrics.
  """

  @property
  def precision(self):
    """
    Calculate and return precision.

    Returns:
      float: Precision.
    """
    if self.metrics.QueryTotal == 0:
      return 0.0
    return self.metrics.QueryTP / self.metrics.QueryTotal

  def confidence_interval(self, method='wilson', **kwargs):
    """
    Calculate the confidence interval for precision.

    Args:
      method (str): Method for confidence interval calculation.
                    Defaults to 'wilson'.
      **kwargs: Additional parameters for the confidence interval method.

    Returns:
      tuple[float, float]: Lower and upper bounds of the confidence interval.
    """
    return ProportionConfidenceInterval.proportion_confidence_interval(
      successes=self.metrics.QueryTP,
      total=self.metrics.QueryTotal,
      method=method,
      **kwargs
    )


class ConcordanceMetrics(SensitivityMetrics, PrecisionMetrics):
  """
  Concordance-related metrics.
  """

  @property
  def concordance(self):
    """
    Calculate and return concordance rate.

    Returns:
      float: Concordance rate.
    """
    total_calls = self.metrics.TruthTotal + self.metrics.QueryFP
    return self.metrics.TruthTP / total_calls if total_calls > 0 else 0

  def confidence_interval(self, method='wilson', **kwargs):
    """
    Calculate the confidence interval for concordance.

    Args:
      method (str): Method for confidence interval calculation.
                    Defaults to 'wilson'.
      **kwargs: Additional parameters for the confidence interval method.

    Returns:
      tuple[float, float]: Lower and upper bounds of the confidence interval.
    """
    total_calls = self.metrics.TruthTotal + self.metrics.QueryFP
    return ProportionConfidenceInterval.proportion_confidence_interval(
      successes=self.metrics.TruthTP,
      total=total_calls,
      method=method,
      **kwargs
    )

  @property
  def f1_score(self):
    """
    Calculate and return the F1 score.

    Returns:
      float: F1 score.
    """
    precision = self.precision
    sensitivity = self.sensitivity
    if precision + sensitivity == 0:
      return 0.0
    return 2 * (precision * sensitivity) / (precision + sensitivity)
