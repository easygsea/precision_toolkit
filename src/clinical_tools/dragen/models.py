"""Data models for parsing DRAGEN metrics."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class DragenMetric:
    """
    Class representing a DRAGEN metric and its properties.

    Attributes:
        metric_group: Top-level metric group (e.g. "MAPPING/ALIGNING SUMMARY").
        name: Metric name (e.g. "MAPPED_READS").
        mapping_spec: Specification for extracting the metric from source file.
        default_val: Default value to use if metric is missing.
        scale_factor: Factor to scale the metric value by.
        scale_factor_op: Operation to apply with the scale factor (e.g., add, multiply
            divide, subtract).
        num_decimal_places: Number of decimal places metric value should have.
        unit: Unit of measurement for the metric.
        fail_threshold: Threshold value for metric to be considered failing.
        fail_direction: Direction relative to threshold for metric value to be
            considered failing.
        other_properties: Dictionary mapping additional properties to corresponding
            values.
    """

    metric_group: str
    name: str
    mapping_spec: dict | str  # dict for CSV source, str for JSON source
    default_val: float | None
    scale_factor: float | None
    scale_factor_op: str
    num_decimal_places: int | None
    unit: str
    fail_threshold: float | None
    fail_direction: str
    other_properties: dict[str, Any]


@dataclass
class SourceFile:
    """
    Class representing a DRAGEN source file and its associated metrics.

    Attributes:
        filename: Name of source file.
        filetype: Type of the source file (e.g., CSV, JSON).
        allow_missing: If True, source file can be missing and associated metrics will
            use default values.
        default_val: Default value to use if the source file or any metrics are
            missing.
        dragen_metrics: Dictionary mapping metric names to DragenMetric objects.
    """

    filename: Path
    filetype: str
    allow_missing: bool
    default_val: float | None
    dragen_metrics: dict[str, DragenMetric]
