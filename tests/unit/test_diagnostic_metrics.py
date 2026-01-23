"""Test variant benchmark diagnostic metrics.

Concordance, Sensitivity, Precision, F1 Score, Confidence Intervals
"""

import pytest

from clinical_tools.core.metrics.variant import (
    ConcordanceMetrics,
    ConcordanceTPMethod,
    F1ScoreMetrics,
    PrecisionMetrics,
    ProportionConfidenceIntervalMethod,
    SensitivityMetrics,
    VariantCallMetrics,
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
    assert sensitivity_metrics.sensitivity == pytest.approx(
        expected_sensitivity, abs=1e-3
    )


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
    assert precision_metrics.precision == pytest.approx(expected_precision, abs=1e-3)


@pytest.mark.parametrize(
    (
        "truth_total, truth_tp, truth_fn, query_total, query_tp, query_fp, "
        "tp_method, expected_concordance"
    ),
    [
        (
            100,
            90,
            10,
            120,
            90,
            30,
            ConcordanceTPMethod.TruthTP.value,
            0.6923,
        ),  # Use TruthTP
        (
            100,
            90,
            10,
            120,
            80,
            30,
            ConcordanceTPMethod.QueryTP.value,
            0.6667,
        ),  # Use QueryTP
        (
            100,
            90,
            10,
            120,
            80,
            30,
            ConcordanceTPMethod.MinTP.value,
            0.6667,
        ),  # Use MinTP (QueryTP is smaller)
        (
            100,
            80,
            20,
            120,
            90,
            30,
            ConcordanceTPMethod.MinTP.value,
            0.6154,
        ),  # Use MinTP (TruthTP is smaller)
        (0, 0, 0, 0, 0, 0, ConcordanceTPMethod.MinTP.value, 0.0),  # Zero total calls
        (100, 0, 100, 120, 0, 120, ConcordanceTPMethod.MinTP.value, 0.0),  # Zero TP
    ],
    ids=[
        "truth_tp",
        "query_tp",
        "min_tp_query",
        "min_tp_truth",
        "zero_total_calls",
        "zero_tp",
    ],
)
def test_concordance_metrics(
    truth_total: int,
    truth_tp: int,
    truth_fn: int,
    query_total: int,
    query_tp: int,
    query_fp: int,
    tp_method: ConcordanceTPMethod,
    expected_concordance: float,
) -> None:
    """
    Test ConcordanceMetrics with parametrized inputs and TP selection methods.

    Execution Order:
    1. Initialize VariantCallMetrics with provided parameters.
    2. Calculate concordance using the specified TP method.
    3. Verify the calculated concordance matches the expected value.

    Expected Behavior:
    - Concordance should be calculated as the selected TP / (TruthTotal + QueryFP).
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
    concordance_metrics = ConcordanceMetrics(metrics, tp_method)
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
    2. Calculate precision and sensitivity.
    3. Calculate F1 score using F1ScoreMetrics.
    4. Verify the calculated F1 score matches the expected value.

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
    precision_metrics = PrecisionMetrics(metrics)
    sensitivity_metrics = SensitivityMetrics(metrics)
    f1_metrics = F1ScoreMetrics(
        precision=precision_metrics.precision,
        sensitivity=sensitivity_metrics.sensitivity,
    )
    assert f1_metrics.f1_score == pytest.approx(expected_f1, rel=1e-3)


@pytest.mark.parametrize(
    "truth_total, truth_tp, truth_fn, ci_method, ci_level, expected_ci",
    [
        (
            100,
            90,
            10,
            ProportionConfidenceIntervalMethod.WILSON,
            0.95,
            (0.826, 0.945),
        ),  # Normal case
        (
            100,
            0,
            100,
            ProportionConfidenceIntervalMethod.WILSON,
            0.95,
            (0.0, 0.037),
        ),  # Zero TP
        (
            0,
            0,
            0,
            ProportionConfidenceIntervalMethod.WILSON,
            0.95,
            (0.0, 0.0),
        ),  # Zero totals
        (
            100,
            100,
            0,
            ProportionConfidenceIntervalMethod.WILSON,
            0.95,
            (0.964, 1.0),
        ),  # Perfect match
        (
            100,
            90,
            10,
            ProportionConfidenceIntervalMethod.AGRESTI_COULL,
            0.95,
            (0.824, 0.946),
        ),  # Normal case agresti coull
        (
            100,
            0,
            100,
            ProportionConfidenceIntervalMethod.AGRESTI_COULL,
            0.95,
            (0.0, 0.0444),
        ),  # Zero TP agresti coull
        (
            0,
            0,
            0,
            ProportionConfidenceIntervalMethod.AGRESTI_COULL,
            0.95,
            (0.0, 0.0),
        ),  # Zero totals agresti coull
        (
            100,
            100,
            0,
            ProportionConfidenceIntervalMethod.AGRESTI_COULL,
            0.95,
            (0.956, 1.0),
        ),  # Perfect match agresti coull
        (
            100,
            90,
            10,
            ProportionConfidenceIntervalMethod.WILSON,
            0.99,
            (0.796, 0.954),
        ),  # Normal case with 99% CI
        (
            100,
            90,
            10,
            ProportionConfidenceIntervalMethod.AGRESTI_COULL,
            0.99,
            (0.793, 0.958),
        ),  # Normal case agresti coull with 99% CI
        (
            100,
            90,
            10,
            ProportionConfidenceIntervalMethod.BETA,
            0.95,
            (0.824, 0.951),
        ),  # Normal case beta
        (
            100,
            90,
            10,
            ProportionConfidenceIntervalMethod.BINOMIAL_TEST,
            0.95,
            (0.826, 0.947),
        ),  # Normal case binomial test
        (
            100,
            90,
            10,
            ProportionConfidenceIntervalMethod.JEFFREYS,
            0.95,
            (0.830, 0.947),
        ),  # Normal case jeffreys
        (
            100,
            90,
            10,
            ProportionConfidenceIntervalMethod.NORMAL,
            0.95,
            (0.841, 0.959),
        ),  # Normal case normal
    ],
    ids=[
        "normal_case",
        "zero_tp",
        "zero_totals",
        "perfect_match",
        "normal_case_agresti_coull",
        "zero_tp_agresti_coull",
        "zero_totals_agresti_coull",
        "perfect_match_agresti_coull",
        "normal_case_99ci",
        "normal_case_agresti_coull_99ci",
        "normal_case_beta",
        "normal_case_binomial_test",
        "normal_case_jeffreys",
        "normal_case_normal",
    ],
)
def test_confidence_interval_sensitivity(
    truth_total: int,
    truth_tp: int,
    truth_fn: int,
    ci_method: ProportionConfidenceIntervalMethod,
    ci_level: float,
    expected_ci: tuple[float, float],
) -> None:
    """
    Test confidence interval calculation for sensitivity with parametrized inputs.

    Execution Order:
    1. Initialize VariantCallMetrics with provided parameters.
    2. Calculate confidence interval for sensitivity.
    3. Verify the confidence interval matches the expected values.

    Expected Behavior:
    - Confidence interval should be calculated
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
        method=ci_method,
        ci_level=ci_level,
    )
    assert ci_lower == pytest.approx(expected_ci[0], abs=0.001)
    assert ci_upper == pytest.approx(expected_ci[1], abs=0.001)
    assert 0 <= ci_lower <= ci_upper <= 1


@pytest.mark.parametrize(
    "query_total, query_tp, query_fp, ci_method, ci_level, expected_ci",
    [
        (
            120,
            90,
            30,
            ProportionConfidenceIntervalMethod.WILSON,
            0.95,
            (0.665, 0.819),
        ),  # Normal case
        (
            120,
            0,
            120,
            ProportionConfidenceIntervalMethod.WILSON,
            0.95,
            (0.0, 0.031),
        ),  # Zero TP
        (
            0,
            0,
            0,
            ProportionConfidenceIntervalMethod.WILSON,
            0.95,
            (0.0, 0.0),
        ),  # Zero totals
        (
            120,
            120,
            0,
            ProportionConfidenceIntervalMethod.WILSON,
            0.95,
            (0.969, 1.0),
        ),  # Perfect match
        (
            120,
            90,
            30,
            ProportionConfidenceIntervalMethod.AGRESTI_COULL,
            0.95,
            (0.665, 0.819),
        ),  # Normal case
        (
            120,
            0,
            120,
            ProportionConfidenceIntervalMethod.AGRESTI_COULL,
            0.95,
            (0.0, 0.0373),
        ),  # Zero TP
        (
            0,
            0,
            0,
            ProportionConfidenceIntervalMethod.AGRESTI_COULL,
            0.95,
            (0.0, 0.0),
        ),  # Zero totals
        (
            120,
            120,
            0,
            ProportionConfidenceIntervalMethod.AGRESTI_COULL,
            0.95,
            (0.963, 1.0),
        ),  # Perfect match
        (
            120,
            90,
            30,
            ProportionConfidenceIntervalMethod.WILSON,
            0.99,
            (0.637, 0.837),
        ),  # Normal case with 99% CI
        (
            120,
            90,
            30,
            ProportionConfidenceIntervalMethod.AGRESTI_COULL,
            0.99,
            (0.636, 0.838),
        ),  # Normal case agresti coull with 99% CI
    ],
    ids=[
        "normal_case",
        "zero_tp",
        "zero_totals",
        "perfect_match",
        "normal_case_agresti_coull",
        "zero_tp_agresti_coull",
        "zero_totals_agresti_coull",
        "perfect_match_agresti_coull",
        "normal_case_99ci",
        "normal_case_agresti_coull_99ci",
    ],
)
def test_confidence_interval_precision(
    query_total: int,
    query_tp: int,
    query_fp: int,
    ci_method: ProportionConfidenceIntervalMethod,
    ci_level: float,
    expected_ci: tuple[float, float],
) -> None:
    """
    Test confidence interval calculation for precision with parametrized inputs.

    Execution Order:
    1. Initialize VariantCallMetrics with provided parameters.
    2. Calculate confidence interval for precision.
    3. Verify the confidence interval matches the expected values.

    Expected Behavior:
    - Confidence interval should be calculated
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
        method=ci_method,
        ci_level=ci_level,
    )
    assert ci_lower == pytest.approx(expected_ci[0], abs=0.001)
    assert ci_upper == pytest.approx(expected_ci[1], abs=0.001)
    assert 0 <= ci_lower <= ci_upper <= 1


@pytest.mark.parametrize(
    (
        "truth_total, truth_tp, truth_fn, "
        "query_total, query_tp, query_fp, "
        "ci_method, ci_level, expected_ci"
    ),
    [
        (
            100,
            90,
            10,
            120,
            90,
            30,
            ProportionConfidenceIntervalMethod.WILSON,
            0.95,
            (0.608, 0.765),
        ),  # Normal case
        (
            100,
            0,
            100,
            120,
            0,
            120,
            ProportionConfidenceIntervalMethod.WILSON,
            0.95,
            (0.0, 0.0172),
        ),  # Zero TP
        (
            0,
            0,
            0,
            0,
            0,
            0,
            ProportionConfidenceIntervalMethod.WILSON,
            0.95,
            (0.0, 0.0),
        ),  # Zero totals
        (
            100,
            100,
            0,
            100,
            100,
            0,
            ProportionConfidenceIntervalMethod.WILSON,
            0.95,
            (0.963, 1.0),
        ),  # Perfect match
        (
            100,
            90,
            10,
            120,
            90,
            30,
            ProportionConfidenceIntervalMethod.AGRESTI_COULL,
            0.95,
            (0.608, 0.765),
        ),  # Normal case
        (
            100,
            0,
            100,
            120,
            0,
            120,
            ProportionConfidenceIntervalMethod.AGRESTI_COULL,
            0.95,
            (0.0, 0.0207),
        ),  # Zero TP
        (
            0,
            0,
            0,
            0,
            0,
            0,
            ProportionConfidenceIntervalMethod.AGRESTI_COULL,
            0.95,
            (0.0, 0.0),
        ),  # Zero totals
        (
            100,
            100,
            0,
            100,
            100,
            0,
            ProportionConfidenceIntervalMethod.AGRESTI_COULL,
            0.95,
            (0.9556, 1.0),
        ),  # Perfect match
        (
            100,
            90,
            10,
            120,
            90,
            30,
            ProportionConfidenceIntervalMethod.WILSON,
            0.99,
            (0.581, 0.785),
        ),  # Normal case with 99% CI
        (
            100,
            90,
            10,
            120,
            90,
            30,
            ProportionConfidenceIntervalMethod.AGRESTI_COULL,
            0.99,
            (0.58, 0.786),
        ),  # Normal case agresti coull with 99% CI
    ],
    ids=[
        "normal_case",
        "zero_tp",
        "zero_totals",
        "perfect_match",
        "normal_case_agresti_coull",
        "zero_tp_agresti_coull",
        "zero_totals_agresti_coull",
        "perfect_match_agresti_coull",
        "normal_case_99ci",
        "normal_case_agresti_coull_99ci",
    ],
)
def test_confidence_interval_concordance(
    truth_total: int,
    truth_tp: int,
    truth_fn: int,
    query_total: int,
    query_tp: int,
    query_fp: int,
    ci_method: ProportionConfidenceIntervalMethod,
    ci_level: float,
    expected_ci: tuple[float, float],
) -> None:
    """
    Test confidence interval calculation for concordance with parametrized inputs.

    Execution Order:
    1. Initialize VariantCallMetrics with provided parameters.
    2. Calculate confidence interval for concordance.
    3. Verify the confidence interval matches the expected values.

    Expected Behavior:
    - Confidence interval should be calculated
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
    concordance_metrics = ConcordanceMetrics(
        metrics, tp_method=ConcordanceTPMethod.MinTP
    )
    ci_lower, ci_upper = concordance_metrics.confidence_interval(
        method=ci_method,
        ci_level=ci_level,
    )
    assert ci_lower == pytest.approx(expected_ci[0], abs=0.001)
    assert ci_upper == pytest.approx(expected_ci[1], abs=0.001)
    assert 0 <= ci_lower <= ci_upper <= 1
