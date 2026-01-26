"""Tests for DRAGEN metrics processing utility functions."""

import pytest

from clinical_tools.dragen.models import DragenMetric
from clinical_tools.dragen.utils import (
    calc_derived_pct_metric,
    classify_metric,
    format_metric,
    scale_metric,
)


@pytest.fixture
def pct_contamination_est() -> DragenMetric:
    """Create a DragenMetric for PCT_CONTAMINATION_EST."""
    return DragenMetric(
        metric_group="MAPPING/ALIGNING SUMMARY",
        name="PCT_CONTAMINATION_EST",
        mapping_spec={"Row": ["Estimated sample contamination", 2], "Col": [3]},
        default_val=None,
        scale_factor=100,
        scale_factor_op="multiply",
        num_decimal_places=2,
        unit="%",
        fail_threshold=0.02,
        fail_direction="greater_than",
        other_properties={},
    )


@pytest.fixture
def pct_contamination_est_none() -> DragenMetric:
    """Create a DragenMetric for PCT_CONTAMINATION_EST with None values."""
    return DragenMetric(
        metric_group="MAPPING/ALIGNING SUMMARY",
        name="PCT_CONTAMINATION_EST",
        mapping_spec={"Row": ["Estimated sample contamination", 2], "Col": [3]},
        default_val=None,
        scale_factor=None,
        scale_factor_op="multiply",
        num_decimal_places=None,
        unit="%",
        fail_threshold=None,
        fail_direction="greater_than",
        other_properties={},
    )


@pytest.fixture
def name_to_metric_obj() -> dict[str, DragenMetric]:
    """Create a dictionary mapping metric names to DragenMetric objects."""
    return {
        "PCT_CHIMERIC_READS_BASE": DragenMetric(
            metric_group="MAPPING/ALIGNING SUMMARY",
            name="PCT_CHIMERIC_READS_BASE",
            mapping_spec={
                "Row": ["Supplementary (chimeric) alignments", 2],
                "Col": [3],
            },
            default_val=None,
            scale_factor=None,
            scale_factor_op="multiply",
            num_decimal_places=None,
            unit="Count",
            fail_threshold=None,
            fail_direction="less_than",
            other_properties={},
        ),
        "PCT_CHIMERIC_READS": DragenMetric(
            metric_group="MAPPING/ALIGNING SUMMARY",
            name="PCT_CHIMERIC_READS",
            mapping_spec={},
            default_val=None,
            scale_factor=100,
            scale_factor_op="multiply",
            num_decimal_places=2,
            unit="%",
            fail_threshold=None,
            fail_direction="less_than",
            other_properties={},
        ),
        "MAPPED_READS": DragenMetric(
            metric_group="MAPPING/ALIGNING SUMMARY",
            name="MAPPED_READS",
            mapping_spec={"Row": ["Mapped reads", 2], "Col": [3]},
            default_val=None,
            scale_factor=0.0001,
            scale_factor_op="add",
            num_decimal_places=None,
            unit="Count",
            fail_threshold=None,
            fail_direction="less_than",
            other_properties={},
        ),
    }


@pytest.mark.parametrize(
    "dragen_metric_fixture,metric_val,expected_name,expected_val",
    [
        ("pct_contamination_est", 0.125, "PCT_CONTAMINATION_EST (%)", "0.13"),
        ("pct_contamination_est_none", 0.0001, "PCT_CONTAMINATION_EST (%)", "0.0001"),
        ("pct_contamination_est", None, "PCT_CONTAMINATION_EST (%)", "None"),
    ],
)
def test_format_metric(
    dragen_metric_fixture: str,
    metric_val: float | None,
    expected_name: str,
    expected_val: float | None,
    request: pytest.FixtureRequest,
) -> None:
    """
    Test format_metric.

    Several scenarios are tested and compared to expected outputs via parametrization:
    - Valid float value and num_decimal_places property set in DragenMetric
    - Valid float value but missing num_decimal_places property in DragenMetric
    - None value
    """
    dragen_metric_obj = request.getfixturevalue(dragen_metric_fixture)
    formatted_name, formatted_val = format_metric(dragen_metric_obj, metric_val)
    assert expected_name == formatted_name
    assert expected_val == formatted_val


@pytest.mark.parametrize(
    "dragen_metric_fixture,metric_val,expected_val",
    [
        ("pct_contamination_est", 0.0001, 0.01),
        ("pct_contamination_est_none", 0.0001, 0.0001),
    ],
)
def test_scale_metric(
    dragen_metric_fixture: str,
    metric_val: float,
    expected_val: float,
    request: pytest.FixtureRequest,
) -> None:
    """
    Test scale_metric.

    Several scenarios are tested and compared to expected outputs via parametrization:
    - Valid float value and scale_factor property set in DragenMetric
    - Valid float value but missing scale_factor property in DragenMetric
    """
    dragen_metric_obj = request.getfixturevalue(dragen_metric_fixture)
    assert expected_val == scale_metric(dragen_metric_obj, metric_val)


@pytest.mark.parametrize(
    "dragen_metric_fixture,metric_val,expected_val",
    [
        ("pct_contamination_est", 0.01, ("Production", "Pass")),
        ("pct_contamination_est_none", 0.01, ("Monitoring", None)),
        ("pct_contamination_est", None, ("Production", "Fail")),
    ],
)
def test_classify_metric(
    dragen_metric_fixture: str,
    metric_val: float | None,
    expected_val: str | None,
    request: pytest.FixtureRequest,
) -> None:
    """
    Test classify_metric.

    Several scenarios are tested and compared to expected outputs via parametrization:
    - Valid float value that passes specified threshold in DragenMetric
    - Valid float value but missing failure properties in DragenMetric
    - None value
    """
    dragen_metric_obj = request.getfixturevalue(dragen_metric_fixture)
    assert expected_val == classify_metric(dragen_metric_obj, metric_val)


@pytest.mark.parametrize(
    "base_metric_val,mapped_reads_val,expected_val",
    [
        (20, 80, 25.0),
        (None, 80, None),
    ],
)
def test_calc_derived_pct_metric(
    name_to_metric_obj: dict[str, DragenMetric],
    base_metric_val: float | None,
    mapped_reads_val: float | None,
    expected_val: float | None,
) -> None:
    """
    Test calc_derived_pct_metric.

    Several scenarios are tested and compared to expected outputs via parametrization:
    - Valid base metric and mapped reads values
    - None base metric value
    """
    all_dragen_metrics = {
        "PCT_CHIMERIC_READS_BASE": base_metric_val,
        "MAPPED_READS": mapped_reads_val,
    }

    calculated_val = calc_derived_pct_metric(
        name_to_metric_obj,
        all_dragen_metrics,
        derived_metric_name="PCT_CHIMERIC_READS",
        base_metric_name="PCT_CHIMERIC_READS_BASE",
    )

    assert expected_val == calculated_val
