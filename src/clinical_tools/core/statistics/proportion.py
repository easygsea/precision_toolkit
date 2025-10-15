"""Proportion confidence interval calculations."""

from enum import StrEnum

from statsmodels.stats.proportion import (  # type: ignore[import-untyped]
    proportion_confint,
)

from clinical_tools.core.constants import (
    DEFAULT_CI_LEVEL,
)


class ProportionConfidenceIntervalMethod(StrEnum):
    """Supported methods for calculating proportion confidence intervals."""

    AGRESTI_COULL = "agresti_coull"
    BETA = "beta"
    BINOMIAL_TEST = "binom_test"
    JEFFREYS = "jeffreys"
    NORMAL = "normal"
    WILSON = "wilson"


class ProportionConfidenceInterval:
    """A class for calculating confidence intervals for proportions."""

    SUPPORTED_METHODS = [method.value for method in ProportionConfidenceIntervalMethod]

    @staticmethod
    def proportion_confidence_interval(
        successes: int,
        total: int,
        method: ProportionConfidenceIntervalMethod = (
            ProportionConfidenceIntervalMethod.WILSON
        ),
        ci_level: float = DEFAULT_CI_LEVEL,
        **kwargs: dict[str, str],
    ) -> tuple[float, float]:
        """Calculate the confidence interval for a binomial proportion.

        Args:
            successes: Number of success events.
            total: Total number of events.
            method: CI calculation method. Must be a ProportionConfidenceIntervalMethod.
            ci_level: Confidence level (default: DEFAULT_CI_LEVEL).
            **kwargs: Additional keyword arguments passed to proportion_confint.

        Returns:
            A tuple containing the lower and upper bounds of the CI.

        Raises:
            ValueError: If method is not supported or confidence level is invalid.
        """
        if method not in ProportionConfidenceInterval.SUPPORTED_METHODS:
            raise ValueError(
                f"Unsupported method '{method}'. "
                f"Available methods are: "
                f"{', '.join(ProportionConfidenceInterval.SUPPORTED_METHODS)}."
            )

        if not 0 < ci_level < 1:
            raise ValueError(
                f"Confidence level must be between 0 and 1. Got {ci_level}."
            )

        if total == 0:
            return (0.0, 0.0)

        return proportion_confint(
            successes, total, method=method, alpha=1 - ci_level, **kwargs
        )
