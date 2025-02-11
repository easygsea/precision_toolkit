from enum import StrEnum
from statsmodels.stats.proportion import proportion_confint


class ProportionConfidenceIntervalMethod(StrEnum):
    """Supported methods for calculating proportion confidence intervals."""

    WILSON = "wilson"
    AGRESTI_COULL = "agresti_coull"
    BETA = "beta"
    JEFFREYS = "jeffreys"
    WALD = "wald"


class ProportionConfidenceInterval:
    """
    A class for calculating confidence intervals for proportions.
    """

    SUPPORTED_METHODS = [method.value for method in ProportionConfidenceIntervalMethod]

    @staticmethod
    def proportion_confidence_interval(successes, total, method="wilson", **kwargs):
        """
        Calculate the confidence interval for a binomial proportion.

        Args:
            successes (int): Number of success events.
            total (int): Total number of events.
            method (str, optional): The method to use for CI calculation.
                                   Defaults to 'wilson'.
            **kwargs: Additional keyword arguments to pass to proportion_confint.

        Returns:
            tuple[float, float]: Lower and upper bounds of the CI.

        Raises:
            ValueError: If the provided method is not supported.
        """
        if method not in ProportionConfidenceInterval.SUPPORTED_METHODS:
            raise ValueError(
                f"Unsupported method '{method}'. "
                f"Available methods are: "
                f"{', '.join(ProportionConfidenceInterval.SUPPORTED_METHODS)}."
            )

        if total == 0:
            return (0.0, 0.0)

        return proportion_confint(successes, total, method=method, **kwargs)
