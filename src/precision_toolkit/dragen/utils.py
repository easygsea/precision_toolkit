"""Utility functions and constants for DRAGEN metrics processing."""

import operator
from decimal import ROUND_HALF_UP, Decimal

from precision_toolkit.dragen.models import DragenMetric

# Valid operations to apply with scale factors
OPERATIONS = {
    "add": operator.add,
    "multiply": operator.mul,
    "divide": operator.truediv,
    "subtract": operator.sub,
    "greater_than": operator.gt,
    "greater_than_or_equal": operator.ge,
    "less_than": operator.lt,
    "less_than_or_equal": operator.le,
}


def format_metric(
    dragen_metric_obj: DragenMetric, metric_val: float | None
) -> tuple[str, str]:
    """Format metric value based on properties stored in DragenMetric object.

    Args:
        dragen_metric_obj: DragenMetric object, corresponding to metric value.
        metric_val: Value to format.

    Returns:
        Tuple of metric name with the format <metric> (<unit>) and metric value with
        specified number of decimal places, represented a a string.
    """
    # Get dragen metric properties
    metric_name = dragen_metric_obj.name
    num_decimal_places = dragen_metric_obj.num_decimal_places
    unit = dragen_metric_obj.unit

    # Apply formatting, if applicable
    formatted_metric_name = f"{metric_name} ({unit})"
    formatted_metric_val = str(metric_val)
    if metric_val is not None and num_decimal_places is not None:
        precision = Decimal(10) ** -num_decimal_places
        rounded_val = Decimal(formatted_metric_val).quantize(
            precision, rounding=ROUND_HALF_UP
        )
        formatted_metric_val = f"{rounded_val:.{num_decimal_places}f}"

    return formatted_metric_name, formatted_metric_val


def scale_metric(dragen_metric_obj: DragenMetric, metric_val: float) -> float:
    """Scale metric value based on properties stored in DragenMetric object.

    Args:
        dragen_metric_obj: DragenMetric object, corresponding to metric value.
        metric_val: Value to scale.

    Returns:
        Transformed metric value after applying scale factor.
    """
    # Get dragen metric properties
    scale_factor = dragen_metric_obj.scale_factor
    scale_factor_op = dragen_metric_obj.scale_factor_op

    scaled_metric_val = metric_val
    if scale_factor is not None:
        scaled_metric_val = OPERATIONS[scale_factor_op](metric_val, scale_factor)
    return scaled_metric_val


def calc_derived_pct_metric(
    metric_to_metric_obj: dict[str, DragenMetric],
    all_dragen_metrics: dict[str, float | None],
    derived_metric_name: str,
    base_metric_name: str,
) -> float | None:
    """Calculate derived percentage metric.

    Takes a base metric value and divides it by the number of mapped reads
    ("MAPPED_READS") to get the percentage.

    Args:
        metric_to_metric_obj: Dictionary mapping metric names to DragenMetric objects.
        all_dragen_metrics: Dictionary mapping metric names to values.
        derived_metric_name: Name of metric to calculate.
        base_metric_name: Name of base metric derived_metric_name is calculated
        from.

    Returns:
        Tuple of formatted metric name and value.
    """
    base_metric_val = all_dragen_metrics[base_metric_name]
    mapped_reads_val = all_dragen_metrics["MAPPED_READS"]
    derived_metric_obj = metric_to_metric_obj[derived_metric_name]

    if base_metric_val is None or mapped_reads_val is None:
        return derived_metric_obj.default_val
    else:
        # Calculate derived metric value
        derived_metric_val = base_metric_val / mapped_reads_val
        return scale_metric(derived_metric_obj, derived_metric_val)


def classify_metric(
    dragen_metric_obj: DragenMetric,
    metric_val: float | None,
) -> tuple[str, str | None]:
    """Classify metric depending on whether value satisfies threshold condition.

    A metric is classified as 'Production' if a fail threshold is defined, otherwise
    it's classified as 'Monitoring'. Production metrics are further evaluated as 'Pass'
    or 'Fail' based on whether the metric value meets the threshold condition.

    Args:
        dragen_metric_obj: DragenMetric object, corresponding to metric value.
        metric_val: Value of to classify.

    Returns:
        Tuple of (category, status) where:
        - category: Either 'Production' or 'Monitoring'.
        - status: Either 'Pass', 'Fail', or None (for Monitoring metrics).
    """
    category = "Monitoring"
    status = None
    if dragen_metric_obj.fail_threshold:
        category = "Production"
        if metric_val is None or OPERATIONS[dragen_metric_obj.fail_direction](
            float(metric_val), dragen_metric_obj.fail_threshold
        ):
            status = "Fail"
        else:
            status = "Pass"

    return category, status
