import json
from typing import Optional

import geopandas
import numpy as np
import rtree
from shapely.geometry import LineString, Point, Polygon

from great_expectations.core.expectation_configuration import ExpectationConfiguration
from great_expectations.exceptions import InvalidExpectationConfigurationError
from great_expectations.execution_engine import (
    PandasExecutionEngine,
    SparkDFExecutionEngine,
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.expectation import ColumnExpectation
from great_expectations.expectations.metrics import (
    ColumnAggregateMetricProvider,
    column_aggregate_value,
)


# This class defines a Metric to support your Expectation.
# For most ColumnMapExpectations, the main business logic for calculation will live in this class.
class ColumnValuesToCheckOverlap(ColumnAggregateMetricProvider):

    # This is the id string that will be used to reference your metric.
    metric_name = "column_values.geometry_not_overlap"

    # This method implements the core logic for the PandasExecutionEngine
    @column_aggregate_value(engine=PandasExecutionEngine)
    def _pandas(cls, column, **kwargs):
        geo_ser = geopandas.GeoSeries(column)
        input_indices, result_indices = geo_ser.sindex.query_bulk(
            geo_ser.geometry, predicate="overlaps"
        )
        overlapping = np.unique(result_indices)  # integer indeces of overlapping
        if np.any(overlapping):
            return {"success": False, "indices": overlapping}
        else:
            return {"success": True}

    # This method defines the business logic for evaluating your metric when using a SqlAlchemyExecutionEngine
    # @column_condition_partial(engine=SqlAlchemyExecutionEngine)
    # def _sqlalchemy(cls, column, _dialect, **kwargs):
    #     raise NotImplementedError

    # This method defines the business logic for evaluating your metric when using a SparkDFExecutionEngine
    # @column_condition_partial(engine=SparkDFExecutionEngine)
    # def _spark(cls, column, **kwargs):
    #     raise NotImplementedError


# This class defines the Expectation itself
class ExpectColumnValuesGeometryNotToOverlap(ColumnExpectation):
    """Expect geometries in this column Not to overlap with each other. If any two geometries do overlap, expectation will return False.
    For more information look here
    https://stackoverflow.com/questions/64042379/shapely-is-valid-returns-true-to-invalid-overlap-polygons"""

    # These examples will be shown in the public gallery.
    # They will also be executed as unit tests for your Expectation.
    examples = [
        {
            "data": {
                "geometry_not_overlaps": [
                    Polygon([(0, 0), (2, 0), (2, 2), (0, 2)]),
                    Polygon([(2, 2), (4, 2), (4, 4), (2, 4)]),
                    Point(5, 6),
                ],
                "geometry_overlaps": [
                    Polygon([(0, 0), (1, 1), (0, 1)]),
                    Polygon([(10, 0), (10, 5), (0, 0)]),
                    Polygon([(0, 0), (2, 2), (2, 0)]),
                ],
            },
            "tests": [
                {
                    "title": "basic_positive_test",
                    "exact_match_out": False,
                    "include_in_gallery": True,
                    "in": {"column": "geometry_not_overlaps"},
                    "out": {"success": True},
                },
                {
                    "title": "basic_negative_test",
                    "exact_match_out": False,
                    "include_in_gallery": True,
                    "in": {"column": "geometry_overlaps"},
                    "out": {"success": False},
                },
            ],
        }
    ]

    # This is the id string of the Metric used by this Expectation.
    # For most Expectations, it will be the same as the `condition_metric_name` defined in your Metric class above.
    metric_dependencies = ("column_values.geometry_not_overlap",)

    # This is a list of parameter names that can affect whether the Expectation evaluates to True or False
    success_keys = ("mostly",)

    # This dictionary contains default values for any parameters that should have default values
    default_kwarg_values = {}

    def validate_configuration(
        self, configuration: Optional[ExpectationConfiguration]
    ) -> None:
        """
        Validates that a configuration has been set, and sets a configuration if it has yet to be set. Ensures that
        necessary configuration arguments have been provided for the validation of the expectation.

        Args:
            configuration (OPTIONAL[ExpectationConfiguration]): \
                An optional Expectation Configuration entry that will be used to configure the expectation
        Returns:
            None. Raises InvalidExpectationConfigurationError if the config is not validated successfully
        """

        super().validate_configuration(configuration)
        if configuration is None:
            configuration = self.configuration

        # # Check other things in configuration.kwargs and raise Exceptions if needed
        # try:
        #     assert (
        #         ...
        #     ), "message"
        #     assert (
        #         ...
        #     ), "message"
        # except AssertionError as e:
        #     raise InvalidExpectationConfigurationError(str(e))

    # This object contains metadata for display in the public Gallery
    def _validate(
        self,
        configuration: ExpectationConfiguration,
        metrics,
        runtime_configuration: dict = None,
        execution_engine=None,
    ):

        success = metrics.get("column_values.geometry_not_overlap").get("success")
        indices = metrics.get("column_values.geometry_not_overlap").get("indices")

        return {"success": success, "result": {"overlapping_indices": indices}}

    library_metadata = {
        "maturity": "experimental",  # "experimental", "beta", or "production"
        "tags": [
            "hackathon-22",
            "geospatial",
        ],  # Tags for this Expectation in the Gallery
        "contributors": [  # Github handles for all contributors to this Expectation.
            "@luismdiaz01",
            "@derekma73",  # Don't forget to add your github handle here!
        ],
        "requirements": ["rtree", "geopandas", "shapely", "numpy"],
    }


if __name__ == "__main__":
    ExpectColumnValuesGeometryNotToOverlap().print_diagnostic_checklist()
