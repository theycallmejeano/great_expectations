from typing import Dict, Union

import numpy as np
import pandas as pd

from great_expectations.rule_based_profiler.helpers.util import (
    compute_bootstrap_quantiles_point_estimate,
)
from great_expectations.rule_based_profiler.parameter_builder import (
    NumericMetricRangeMultiBatchParameterBuilder,
)

# Allowable tolerance for how closely a bootstrap method approximates the sample
from great_expectations.rule_based_profiler.types import NumericRangeEstimationResult

EFFICACY_TOLERANCE: float = 1.0e-2

# Measure of "closeness" between "actual" and "desired" is computed as: atol + rtol * abs(desired)
# (see "https://numpy.org/doc/stable/reference/generated/numpy.testing.assert_allclose.html" for details).
RTOL: float = 1.0e-7
ATOL: float = 1.0e-2


def test_bootstrap_point_estimate_efficacy(
    bootstrap_distribution_parameters_and_1000_samples_with_01_false_positive,
):
    """
    Efficacy means the custom bootstrap mean method approximates the sample +/- efficacy tolerance
    """
    false_positive_rate: np.float64 = (
        bootstrap_distribution_parameters_and_1000_samples_with_01_false_positive[
            "false_positive_rate"
        ]
    )
    distribution_samples: pd.DataFrame = (
        bootstrap_distribution_parameters_and_1000_samples_with_01_false_positive[
            "distribution_samples"
        ]
    )

    distribution_types: pd.Index = distribution_samples.columns
    distribution: str
    numeric_range_estimation_result: NumericRangeEstimationResult
    lower_quantile_point_estimate: np.float64
    upper_quantile_point_estimate: np.float64
    actual_false_positive_rates: Dict[str, Union[float, np.float64]] = {}
    for distribution in distribution_types:
        numeric_range_estimation_result = compute_bootstrap_quantiles_point_estimate(
            metric_values=distribution_samples[distribution],
            false_positive_rate=false_positive_rate,
            n_resamples=NumericMetricRangeMultiBatchParameterBuilder.DEFAULT_BOOTSTRAP_NUM_RESAMPLES,
            quantile_statistic_interpolation_method="linear",
            quantile_bias_std_error_ratio_threshold=2.5e-1,
        )
        lower_quantile_point_estimate = numeric_range_estimation_result.value_range[0]
        upper_quantile_point_estimate = numeric_range_estimation_result.value_range[1]
        actual_false_positive_rates[distribution] = (
            1.0
            - np.sum(
                distribution_samples[distribution].between(
                    lower_quantile_point_estimate, upper_quantile_point_estimate
                )
            )
            / distribution_samples.shape[0]
        )
        # Actual false-positives must be within the efficacy tolerance of desired (configured)
        # false_positive_rate parameter value.
        np.testing.assert_allclose(
            actual=actual_false_positive_rates[distribution],
            desired=false_positive_rate,
            rtol=RTOL,
            atol=EFFICACY_TOLERANCE,
            err_msg=f"Actual value of {actual_false_positive_rates[distribution]} differs from expected value of {false_positive_rate} by more than {ATOL + EFFICACY_TOLERANCE * abs(actual_false_positive_rates[distribution])} tolerance.",
        )
