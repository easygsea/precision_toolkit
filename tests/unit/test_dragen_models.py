"""Tests for DRAGEN metrics data models."""

import pytest

from precision_toolkit.dragen.models import DragenMetric


@pytest.mark.parametrize(
    "fail_threshold,fail_direction,other_properties,expected_lsl,expected_usl",
    [
        (0.02, "greater_than", {}, None, 0.02),
        (0.02, "greater_than_or_equal", {}, None, 0.02),
        (5, "less_than", {}, 5, None),
        (5, "less_than_or_equal", {}, 5, None),
        (5, "less_than", {"LSL": 3.0}, 3.0, None),
        (0.02, "greater_than", {"USL": 0.03}, None, 0.03),
        (None, "", {}, None, None),
    ],
    ids=[
        "usl_gt",
        "usl_gte",
        "lsl_lt",
        "lsl_lte",
        "configured_lsl_overrides_threshold",
        "configured_usl_overrides_threshold",
        "no_threshold",
    ],
)
def test_lsl_usl(
    fail_threshold: float | None,
    fail_direction: str,
    other_properties: dict[str, float],
    expected_lsl: float | None,
    expected_usl: float | None,
) -> None:
    """Test lsl and usl are derived from fail threshold and direction.

    Several scenarios are tested and compared to expected outputs via parametrization:
    - Thresholds with a greater_than direction are reported as the upper limit
    - Thresholds with a less_than direction are reported as the lower limit
    - No threshold or direction sets neither limit
    """
    metric = DragenMetric(
        metric_group="MAPPING/ALIGNING SUMMARY",
        name="TEST_METRIC",
        mapping_spec={},
        default_val=None,
        scale_factor=None,
        scale_factor_op="",
        num_decimal_places=None,
        unit="",
        fail_threshold=fail_threshold,
        fail_direction=fail_direction,
        other_properties=other_properties,
    )

    assert metric.lsl == expected_lsl
    assert metric.usl == expected_usl
