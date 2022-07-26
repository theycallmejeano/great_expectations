import dataprofiler as dp

from great_expectations.execution_engine import PandasExecutionEngine
from great_expectations.expectations.metrics.metric_provider import metric_value

from .data_profiler_profile_metric_provider import DataProfilerProfileMetricProvider


class DataProfilerProfileReport(DataProfilerProfileMetricProvider):
    metric_name = "data_profiler.profile_report"

    value_keys = ("profile_path",)

    @metric_value(engine=PandasExecutionEngine)
    def _pandas(
        cls,
        execution_engine,
        metric_domain_kwargs,
        metric_value_kwargs,
        metrics,
        runtime_configuration,
    ):
        profile_path = metric_value_kwargs["profile_path"]
        try:
            profile = dp.Profiler.load(profile_path)
            profile_report = profile.report(
                report_options={"output_format": "serializable"}
            )
            profile_report["global_stats"]["profile_schema"] = dict(
                profile_report["global_stats"]["profile_schema"]
            )
            return profile_report
        except FileNotFoundError:
            raise ValueError(
                "'profile_path' does not point to a valid DataProfiler stored profile."
            )
