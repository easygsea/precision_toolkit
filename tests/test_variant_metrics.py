"""Test variant metrics."""

import pytest

from clinical_tools.core.metrics.variant import (
    ConcordanceMetrics,
    PrecisionMetrics,
    ProportionConfidenceIntervalMethod,
    SensitivityMetrics,
    VariantCallMetrics,
)


@pytest.fixture
def sample_metrics() -> VariantCallMetrics:
    """Fixture providing sample variant call metrics."""
    return VariantCallMetrics(
        VariantType="SNV",
        VariantCallFilter="PASS",
        TruthTotal=100,
        TruthTP=90,
        TruthFN=10,
        QueryTotal=120,
        QueryTP=90,
        QueryFP=30,
    )


@pytest.mark.parametrize(
    "truth_total, truth_tp, truth_fn, expected_sensitivity",
    [
        (100, 90, 10, 0.9),  # Normal case
        (0, 0, 0, 0.0),  # Zero TruthTotal
        (100, 0, 100, 0.0),  # Zero TruthTP
        (100, 100, 0, 1.0),  # Perfect sensitivity (zero TruthFN)
    ],
    ids=["normal_case", "zero_truth_total", "zero_truth_tp", "perfect_sensitivity"],
)
def test_sensitivity_metrics(
    truth_total: int,
    truth_tp: int,
    truth_fn: int,
    expected_sensitivity: float,
) -> None:
    """
    Test SensitivityMetrics with parametrized inputs.

    Execution Order:
    1. Initialize VariantCallMetrics with provided parameters.
    2. Calculate sensitivity.
    3. Verify the calculated sensitivity matches the expected value.

    Expected Behavior:
    - Sensitivity should be calculated as TruthTP / TruthTotal.
    """
    metrics = VariantCallMetrics(
        VariantType="SNV",
        VariantCallFilter="PASS",
        TruthTotal=truth_total,
        TruthTP=truth_tp,
        TruthFN=truth_fn,
        QueryTotal=120,
        QueryTP=90,
        QueryFP=30,
    )
    sensitivity_metrics = SensitivityMetrics(metrics)
    assert sensitivity_metrics.sensitivity == expected_sensitivity


@pytest.mark.parametrize(
    "query_total, query_tp, query_fp, expected_precision",
    [
        (120, 90, 30, 0.75),  # Normal case
        (0, 0, 0, 0.0),  # Zero QueryTotal
        (120, 0, 120, 0.0),  # Zero QueryTP
        (120, 120, 0, 1.0),  # Perfect precision (zero QueryFP)
    ],
    ids=["normal_case", "zero_query_total", "zero_query_tp", "perfect_precision"],
)
def test_precision_metrics(
    query_total: int,
    query_tp: int,
    query_fp: int,
    expected_precision: float,
) -> None:
    """
    Test PrecisionMetrics with parametrized inputs.

    Execution Order:
    1. Initialize VariantCallMetrics with provided parameters.
    2. Calculate precision.
    3. Verify the calculated precision matches the expected value.

    Expected Behavior:
    - Precision should be calculated as QueryTP / QueryTotal.
    """
    metrics = VariantCallMetrics(
        VariantType="SNV",
        VariantCallFilter="PASS",
        TruthTotal=100,
        TruthTP=90,
        TruthFN=10,
        QueryTotal=query_total,
        QueryTP=query_tp,
        QueryFP=query_fp,
    )
    precision_metrics = PrecisionMetrics(metrics)
    assert precision_metrics.precision == expected_precision


@pytest.mark.parametrize(
    "truth_total, truth_tp, truth_fn, query_total, query_tp, query_fp, expected_concordance",
    [
        (100, 90, 10, 120, 90, 30, 0.6923),  # Normal case
        (0, 0, 0, 0, 0, 0, 0.0),  # Zero total calls
        (100, 0, 100, 120, 0, 120, 0.0),  # Zero TruthTP
    ],
    ids=["normal_case", "zero_total_calls", "zero_truth_tp"],
)
def test_concordance_metrics(
    truth_total: int,
    truth_tp: int,
    truth_fn: int,
    query_total: int,
    query_tp: int,
    query_fp: int,
    expected_concordance: float,
) -> None:
    """
    Test ConcordanceMetrics with parametrized inputs.

    Execution Order:
    1. Initialize VariantCallMetrics with provided parameters.
    2. Calculate concordance.
    3. Verify the calculated concordance matches the expected value.

    Expected Behavior:
    - Concordance should be calculated as TruthTP / (TruthTotal + QueryFP).
    """
    metrics = VariantCallMetrics(
        VariantType="SNV",
        VariantCallFilter="PASS",
        TruthTotal=truth_total,
        TruthTP=truth_tp,
        TruthFN=truth_fn,
        QueryTotal=query_total,
        QueryTP=query_tp,
        QueryFP=query_fp,
    )
    concordance_metrics = ConcordanceMetrics(metrics)
    assert concordance_metrics.concordance == pytest.approx(
        expected_concordance, rel=1e-3
    )


@pytest.mark.parametrize(
    "truth_total, truth_tp, truth_fn, query_total, query_tp, query_fp, expected_f1",
    [
        (100, 90, 10, 120, 90, 30, 0.8182),  # Normal case
        (100, 0, 100, 120, 0, 120, 0.0),  # Zero TP
        (0, 0, 0, 0, 0, 0, 0.0),  # Zero totals
        (100, 100, 0, 100, 100, 0, 1.0),  # Perfect match
    ],
    ids=["normal_case", "zero_tp", "zero_totals", "perfect_match"],
)
def test_f1_score(
    truth_total: int,
    truth_tp: int,
    truth_fn: int,
    query_total: int,
    query_tp: int,
    query_fp: int,
    expected_f1: float,
) -> None:
    """
    Test F1 score calculation with parametrized inputs.

    Execution Order:
    1. Initialize VariantCallMetrics with provided parameters.
    2. Calculate F1 score.
    3. Verify the calculated F1 score matches the expected value.

    Expected Behavior:
    - F1 score should be calculated as the harmonic mean of precision and sensitivity.
    """
    metrics = VariantCallMetrics(
        VariantType="SNV",
        VariantCallFilter="PASS",
        TruthTotal=truth_total,
        TruthTP=truth_tp,
        TruthFN=truth_fn,
        QueryTotal=query_total,
        QueryTP=query_tp,
        QueryFP=query_fp,
    )
    concordance_metrics = ConcordanceMetrics(metrics)
    assert concordance_metrics.f1_score == pytest.approx(expected_f1, rel=1e-3)


@pytest.mark.parametrize(
    "truth_total, truth_tp, truth_fn, expected_ci",
    [
        (100, 90, 10, (0.826, 0.945)),  # Normal case
        (100, 0, 100, (0.0, 0.037)),  # Zero TP
        (0, 0, 0, (0.0, 0.0)),  # Zero totals
        (100, 100, 0, (0.964, 1.0)),  # Perfect match
    ],
    ids=["normal_case", "zero_tp", "zero_totals", "perfect_match"],
)
def test_confidence_interval_sensitivity(
    truth_total: int,
    truth_tp: int,
    truth_fn: int,
    expected_ci: tuple[float, float],
) -> None:
    """
    Test confidence interval calculation for sensitivity with parametrized inputs.

    Execution Order:
    1. Initialize VariantCallMetrics with provided parameters.
    2. Calculate confidence interval for sensitivity using Wilson score interval method.
    3. Verify the confidence interval matches the expected values.

    Expected Behavior:
    - Confidence interval should be calculated using Wilson score interval method
    - Confidence interval should match the pre-calculated expected values
    - Values should be within 0 and 1
    """
    metrics = VariantCallMetrics(
        VariantType="SNV",
        VariantCallFilter="PASS",
        TruthTotal=truth_total,
        TruthTP=truth_tp,
        TruthFN=truth_fn,
        QueryTotal=100,
        QueryTP=90,
        QueryFP=10,
    )
    sensitivity_metrics = SensitivityMetrics(metrics)
    ci_lower, ci_upper = sensitivity_metrics.confidence_interval(
        method=ProportionConfidenceIntervalMethod.WILSON
    )
    assert ci_lower == pytest.approx(expected_ci[0], abs=0.001)
    assert ci_upper == pytest.approx(expected_ci[1], abs=0.001)
    assert 0 <= ci_lower <= ci_upper <= 1


@pytest.mark.parametrize(
    "query_total, query_tp, query_fp, expected_ci",
    [
        (120, 90, 30, (0.665, 0.819)),  # Normal case
        (120, 0, 120, (0.0, 0.031)),  # Zero TP
        (0, 0, 0, (0.0, 0.0)),  # Zero totals
        (100, 100, 0, (0.964, 1.0)),  # Perfect match
    ],
    ids=["normal_case", "zero_tp", "zero_totals", "perfect_match"],
)
def test_confidence_interval_precision(
    query_total: int,
    query_tp: int,
    query_fp: int,
    expected_ci: tuple[float, float],
) -> None:
    """
    Test confidence interval calculation for precision with parametrized inputs.

    Execution Order:
    1. Initialize VariantCallMetrics with provided parameters.
    2. Calculate confidence interval for precision using Wilson score interval method.
    3. Verify the confidence interval matches the expected values.

    Expected Behavior:
    - Confidence interval should be calculated using Wilson score interval method
    - Confidence interval should match the pre-calculated expected values
    - Values should be within 0 and 1
    """
    metrics = VariantCallMetrics(
        VariantType="SNV",
        VariantCallFilter="PASS",
        TruthTotal=100,
        TruthTP=90,
        TruthFN=10,
        QueryTotal=query_total,
        QueryTP=query_tp,
        QueryFP=query_fp,
    )
    precision_metrics = PrecisionMetrics(metrics)
    ci_lower, ci_upper = precision_metrics.confidence_interval(
        method=ProportionConfidenceIntervalMethod.WILSON
    )
    assert ci_lower == pytest.approx(expected_ci[0], abs=0.001)
    assert ci_upper == pytest.approx(expected_ci[1], abs=0.001)
    assert 0 <= ci_lower <= ci_upper <= 1


@pytest.mark.parametrize(
    "truth_total, truth_tp, truth_fn, query_total, query_tp, query_fp, expected_ci",
    [
        (100, 90, 10, 120, 90, 30, (0.608, 0.765)),  # Normal case
        (100, 0, 100, 120, 0, 120, (0.0, 0.017)),  # Zero TP
        (0, 0, 0, 0, 0, 0, (0.0, 0.0)),  # Zero totals
        (100, 100, 0, 100, 100, 0, (0.964, 1.0)),  # Perfect match
    ],
    ids=["normal_case", "zero_tp", "zero_totals", "perfect_match"],
)
def test_confidence_interval_concordance(
    truth_total: int,
    truth_tp: int,
    truth_fn: int,
    query_total: int,
    query_tp: int,
    query_fp: int,
    expected_ci: tuple[float, float],
) -> None:
    """
    Test confidence interval calculation for concordance with parametrized inputs.

    Execution Order:
    1. Initialize VariantCallMetrics with provided parameters.
    2. Calculate confidence interval for concordance using Wilson score interval method.
    3. Verify the confidence interval matches the expected values.

    Expected Behavior:
    - Confidence interval should be calculated using Wilson score interval method
    - Confidence interval should match the pre-calculated expected values
    - Values should be within 0 and 1
    """
    metrics = VariantCallMetrics(
        VariantType="SNV",
        VariantCallFilter="PASS",
        TruthTotal=truth_total,
        TruthTP=truth_tp,
        TruthFN=truth_fn,
        QueryTotal=query_total,
        QueryTP=query_tp,
        QueryFP=query_fp,
    )
    concordance_metrics = ConcordanceMetrics(metrics)
    ci_lower, ci_upper = concordance_metrics.confidence_interval(
        method=ProportionConfidenceIntervalMethod.WILSON
    )
    assert ci_lower == pytest.approx(expected_ci[0], abs=0.001)
    assert ci_upper == pytest.approx(expected_ci[1], abs=0.001)
    assert 0 <= ci_lower <= ci_upper <= 1
