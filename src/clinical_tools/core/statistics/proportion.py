from statsmodels.stats.proportion import proportion_confint


class ProportionConfidenceInterval:
    """
    A class for calculating confidence intervals for proportions.
    """

    SUPPORTED_METHODS = ["wilson", "agresti_coull", "beta", "jeffreys", "wald"]

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
