import os
import shutil
from typing import List, Union

import pandas as pd
import pytest

from great_expectations.core.batch import Batch, BatchRequest
from great_expectations.core.yaml_handler import YAMLHandler
from great_expectations.data_context.util import file_relative_path
from great_expectations.exceptions import InvalidBatchRequestError
from great_expectations.validator.validator import Validator
from tests.test_utils import create_files_in_directory

yaml = YAMLHandler()


@pytest.fixture
def context_with_single_titanic_csv(empty_data_context, tmp_path_factory):
    context = empty_data_context

    base_directory = str(
        tmp_path_factory.mktemp(
            "test_get_batch_list_from_new_style_datasource_with_file_system_datasource_configured_assets"
        )
    )

    titanic_asset_base_directory_path: str = os.path.join(base_directory, "data")
    os.makedirs(titanic_asset_base_directory_path)

    titanic_csv_source_file_path: str = file_relative_path(
        __file__, "../../test_sets/Titanic.csv"
    )
    titanic_csv_destination_file_path: str = str(
        os.path.join(base_directory, "data/Titanic_19120414_1313.csv")
    )
    shutil.copy(titanic_csv_source_file_path, titanic_csv_destination_file_path)

    config = yaml.load(
        f"""
        class_name: Datasource

        execution_engine:
            class_name: PandasExecutionEngine

        data_connectors:
            my_data_connector:
                class_name: ConfiguredAssetFilesystemDataConnector
                base_directory: {base_directory}
                glob_directive: "*.csv"

                default_regex:
                    pattern: (.+)\\.csv
                    group_names:
                        - name
                assets:
                    Titanic:
                        base_directory: {titanic_asset_base_directory_path}
                        pattern: (.+)_(\\d+)_(\\d+)\\.csv
                        group_names:
                            - name
                            - timestamp
                            - size
            """,
    )

    context.add_datasource(
        "my_datasource",
        **config,
    )
    return context


def test_get_validator(context_with_single_titanic_csv):
    context: "DataContext" = context_with_single_titanic_csv
    batch_request_dict: Union[dict, BatchRequest] = {
        "datasource_name": "my_datasource",
        "data_connector_name": "my_data_connector",
        "data_asset_name": "Titanic",
    }
    batch_request: BatchRequest = BatchRequest(**batch_request_dict)
    context.create_expectation_suite(expectation_suite_name="temp_suite")
    my_validator: Validator = context.get_validator(
        batch_request=batch_request, expectation_suite_name="temp_suite"
    )
    assert isinstance(my_validator, Validator)
    assert len(my_validator.batches) == 1
    assert my_validator.active_batch.data.dataframe.shape == (1313, 7)


def test_get_validator_bad_batch_request(context_with_single_titanic_csv):
    context: "DataContext" = context_with_single_titanic_csv
    batch_request_dict: Union[dict, BatchRequest] = {
        "datasource_name": "my_datasource",
        "data_connector_name": "my_data_connector",
        "data_asset_name": "I_DONT_EXIST",
    }
    batch_request: BatchRequest = BatchRequest(**batch_request_dict)
    context.create_expectation_suite(expectation_suite_name="temp_suite")
    with pytest.raises(InvalidBatchRequestError):
        context.get_validator(
            batch_request=batch_request, expectation_suite_name="temp_suite"
        )


def test_get_batch_list_from_new_style_datasource_with_file_system_datasource_inferred_assets(
    empty_data_context, tmp_path_factory
):
    context = empty_data_context

    base_directory = str(
        tmp_path_factory.mktemp(
            "test_get_batch_list_from_new_style_datasource_with_file_system_datasource_inferred_assets"
        )
    )
    create_files_in_directory(
        directory=base_directory,
        file_name_list=[
            "path/A-100.csv",
            "path/A-101.csv",
            "directory/B-1.csv",
            "directory/B-2.csv",
        ],
        file_content_fn=lambda: "x,y,z\n1,2,3\n2,3,5",
    )

    config = yaml.load(
        f"""
class_name: Datasource

execution_engine:
    class_name: PandasExecutionEngine

data_connectors:
    my_data_connector:
        class_name: InferredAssetFilesystemDataConnector
        base_directory: {base_directory}
        glob_directive: "*/*.csv"

        default_regex:
            pattern: (.+)/(.+)-(\\d+)\\.csv
            group_names:
                - data_asset_name
                - letter
                - number
    """,
    )

    context.add_datasource(
        "my_datasource",
        **config,
    )

    batch_request: Union[dict, BatchRequest] = {
        "datasource_name": "my_datasource",
        "data_connector_name": "my_data_connector",
        "data_asset_name": "path",
        "data_connector_query": {
            "batch_filter_parameters": {
                # "data_asset_name": "path",
                "letter": "A",
                "number": "101",
            }
        },
    }
    batch_list: List[Batch] = context.get_batch_list(**batch_request)

    assert len(batch_list) == 1

    batch: Batch = batch_list[0]
    assert batch.batch_spec is not None
    assert batch.batch_definition["data_asset_name"] == "path"
    assert batch.batch_definition["batch_identifiers"] == {
        "letter": "A",
        "number": "101",
    }
    assert isinstance(batch.data.dataframe, pd.DataFrame)
    assert batch.data.dataframe.shape == (2, 3)


def test_get_batch_list_from_new_style_datasource_with_file_system_datasource_configured_assets(
    context_with_single_titanic_csv,
):
    context = context_with_single_titanic_csv

    batch_request: Union[dict, BatchRequest] = {
        "datasource_name": "my_datasource",
        "data_connector_name": "my_data_connector",
        "data_asset_name": "Titanic",
        "data_connector_query": {
            "batch_filter_parameters": {
                "name": "Titanic",
                "timestamp": "19120414",
                "size": "1313",
            }
        },
    }
    batch_list: List[Batch] = context.get_batch_list(**batch_request)

    assert len(batch_list) == 1

    batch: Batch = batch_list[0]
    assert batch.batch_spec is not None
    assert batch.batch_definition["data_asset_name"] == "Titanic"
    assert batch.batch_definition["batch_identifiers"] == {
        "name": "Titanic",
        "timestamp": "19120414",
        "size": "1313",
    }
    assert isinstance(batch.data.dataframe, pd.DataFrame)
    assert batch.data.dataframe.shape == (1313, 7)


def test_get_batch_list_from_new_style_datasource_with_runtime_data_connector(
    empty_data_context, tmp_path_factory
):
    context = empty_data_context
    config = yaml.load(
        """
class_name: Datasource

execution_engine:
    class_name: PandasExecutionEngine

data_connectors:
    test_runtime_data_connector:
        module_name: great_expectations.datasource.data_connector
        class_name: RuntimeDataConnector
        batch_identifiers:
            - airflow_run_id
    """,
    )

    context.add_datasource(
        "my_datasource",
        **config,
    )

    test_df: pd.DataFrame = pd.DataFrame(data={"col1": [1, 2], "col2": [3, 4]})
    data_connector_name: str = "test_runtime_data_connector"
    data_asset_name: str = "test_asset_1"

    batch_request: dict = {
        "datasource_name": "my_datasource",
        "data_connector_name": data_connector_name,
        "data_asset_name": data_asset_name,
        "runtime_parameters": {
            "batch_data": test_df,
        },
        "batch_identifiers": {
            "airflow_run_id": 1234567890,
        },
    }

    batch_list = context.get_batch_list(**batch_request)
    assert len(batch_list) == 1

    batch: Batch = batch_list[0]
    assert batch.batch_spec is not None
    assert batch.batch_definition["data_asset_name"] == "test_asset_1"
    assert batch.batch_definition["batch_identifiers"] == {
        "airflow_run_id": 1234567890,
    }
    assert isinstance(batch.data.dataframe, pd.DataFrame)
    assert batch.data.dataframe.shape == (2, 2)


def test_get_batch_list_from_new_style_datasource_with_file_system_datasource_configured_assets_testing_query(
    empty_data_context, tmp_path_factory
):
    context = empty_data_context
    base_directory = str(
        tmp_path_factory.mktemp(
            "test_get_batch_list_from_new_style_datasource_with_file_system_datasource_configured_assets_queries"
        )
    )
    create_files_in_directory(
        directory=base_directory,
        file_name_list=[
            "Test_1998.csv",
            "Test_1999.csv",
            "Test_2000.csv",
            "Test_2010.csv",
            "Test_2021.csv",
        ],
        file_content_fn=lambda: "x,y,z\n1,2,3\n2,3,5",
    )

    config = yaml.load(
        f"""
    class_name: Datasource

    execution_engine:
        class_name: PandasExecutionEngine

    data_connectors:
        my_data_connector:
            class_name: ConfiguredAssetFilesystemDataConnector
            base_directory: {base_directory}
            glob_directive: "*.csv"

            default_regex:
                pattern: (.+)_(\\d.*)\\.csv
                group_names:
                    - name
                    - year
            sorters:
                - orderby: desc
                  class_name: NumericSorter
                  name: year
            assets:
                YearTest:
                    base_directory: {base_directory}
                    pattern: (.+)_(\\d.*)\\.csv
                    group_names:
                        - name
                        - year

        """,
    )
    context.add_datasource(
        "my_datasource",
        **config,
    )

    # only select files from after 2000
    def my_custom_batch_selector(batch_identifiers: dict) -> bool:
        return int(batch_identifiers["year"]) > 2000

    batch_request: Union[dict, BatchRequest] = {
        "datasource_name": "my_datasource",
        "data_connector_name": "my_data_connector",
        "data_asset_name": "YearTest",
        "data_connector_query": {
            "custom_filter_function": my_custom_batch_selector,
        },
    }

    batch_list: List[Batch] = context.get_batch_list(**batch_request)
    assert len(batch_list) == 2

    # first batch
    batch: Batch = batch_list[0]
    assert batch.batch_spec is not None
    assert batch.batch_definition["data_asset_name"] == "YearTest"
    assert batch.batch_definition["batch_identifiers"] == {
        "name": "Test",
        "year": "2021",
    }

    # second batch
    batch: Batch = batch_list[1]
    assert batch.batch_spec is not None
    assert batch.batch_definition["data_asset_name"] == "YearTest"
    assert batch.batch_definition["batch_identifiers"] == {
        "name": "Test",
        "year": "2010",
    }


def test_get_batch_list_from_new_style_datasource_with_file_system_datasource_configured_assets_testing_limit_and_custom_filter(
    empty_data_context, tmp_path_factory
):
    context = empty_data_context
    base_directory = str(
        tmp_path_factory.mktemp(
            "test_get_batch_list_from_new_style_datasource_with_file_system_datasource_configured_assets_testing_limit_and_custom_filter"
        )
    )
    create_files_in_directory(
        directory=base_directory,
        file_name_list=[
            "Test_1998.csv",
            "Test_1999.csv",
            "Test_2000.csv",
            "Test_2010.csv",
            "Test_2021.csv",
        ],
        file_content_fn=lambda: "x,y,z\n1,2,3\n2,3,5",
    )

    config = yaml.load(
        f"""
    class_name: Datasource

    execution_engine:
        class_name: PandasExecutionEngine

    data_connectors:
        my_data_connector:
            class_name: ConfiguredAssetFilesystemDataConnector
            base_directory: {base_directory}
            glob_directive: "*.csv"

            default_regex:
                pattern: (.+)_(\\d.*)\\.csv
                group_names:
                    - name
                    - year
            sorters:
                - orderby: desc
                  class_name: NumericSorter
                  name: year
            assets:
                YearTest:
                    base_directory: {base_directory}
                    pattern: (.+)_(\\d.*)\\.csv
                    group_names:
                        - name
                        - year

        """,
    )
    context.add_datasource(
        "my_datasource",
        **config,
    )

    # only select files from 1999 or later
    def my_custom_batch_selector(batch_identifiers: dict) -> bool:
        return int(batch_identifiers["year"]) >= 1999

    # Use an instantiated BatchRequest object with custom filter AND limit
    batch_request: BatchRequest = BatchRequest(
        datasource_name="my_datasource",
        data_connector_name="my_data_connector",
        data_asset_name="YearTest",
        data_connector_query={"custom_filter_function": my_custom_batch_selector},
        limit=2,
    )

    batch_list: List[Batch] = context.get_batch_list(batch_request=batch_request)
    assert len(batch_list) == 2

    # first batch
    batch: Batch = batch_list[0]
    assert batch.batch_spec is not None
    assert batch.batch_definition["data_asset_name"] == "YearTest"
    assert batch.batch_definition["batch_identifiers"] == {
        "name": "Test",
        "year": "2021",
    }

    # second batch
    batch: Batch = batch_list[1]
    assert batch.batch_spec is not None
    assert batch.batch_definition["data_asset_name"] == "YearTest"
    assert batch.batch_definition["batch_identifiers"] == {
        "name": "Test",
        "year": "2010",
    }


def test_get_batch_list_from_new_style_datasource_with_file_system_datasource_configured_assets_testing_limit_and_custom_filter_limit_param_ignored(
    empty_data_context, tmp_path_factory
):
    """
    What does this test and why?
    This test mirrors other tests in this file but the key difference is that it tests whether a limit parameter passed in as a part of the data_connector_query overrides a limit passed in as a parameter to the BatchRequest.
    """
    context = empty_data_context
    base_directory = str(
        tmp_path_factory.mktemp(
            "test_get_batch_list_from_new_style_datasource_with_file_system_datasource_configured_assets_testing_limit_and_custom_filter"
        )
    )
    create_files_in_directory(
        directory=base_directory,
        file_name_list=[
            "Test_1998.csv",
            "Test_1999.csv",
            "Test_2000.csv",
            "Test_2010.csv",
            "Test_2021.csv",
        ],
        file_content_fn=lambda: "x,y,z\n1,2,3\n2,3,5",
    )

    config = yaml.load(
        f"""
    class_name: Datasource

    execution_engine:
        class_name: PandasExecutionEngine

    data_connectors:
        my_data_connector:
            class_name: ConfiguredAssetFilesystemDataConnector
            base_directory: {base_directory}
            glob_directive: "*.csv"

            default_regex:
                pattern: (.+)_(\\d.*)\\.csv
                group_names:
                    - name
                    - year
            sorters:
                - orderby: desc
                  class_name: NumericSorter
                  name: year
            assets:
                YearTest:
                    base_directory: {base_directory}
                    pattern: (.+)_(\\d.*)\\.csv
                    group_names:
                        - name
                        - year

        """,
    )
    context.add_datasource(
        "my_datasource",
        **config,
    )

    # only select files from 1999 or later
    def my_custom_batch_selector(batch_identifiers: dict) -> bool:
        return int(batch_identifiers["year"]) >= 1999

    # Use an instantiated BatchRequest object with custom filter AND limit
    # limit in data_connector_query should override the limit in the constructor
    batch_request: BatchRequest = BatchRequest(
        datasource_name="my_datasource",
        data_connector_name="my_data_connector",
        data_asset_name="YearTest",
        data_connector_query={
            "custom_filter_function": my_custom_batch_selector,
            "limit": 3,
        },
        limit=2,
    )

    batch_list: List[Batch] = context.get_batch_list(batch_request=batch_request)
    assert len(batch_list) == 3

    # first batch
    batch: Batch = batch_list[0]
    assert batch.batch_spec is not None
    assert batch.batch_definition["data_asset_name"] == "YearTest"
    assert batch.batch_definition["batch_identifiers"] == {
        "name": "Test",
        "year": "2021",
    }

    # second batch
    batch: Batch = batch_list[1]
    assert batch.batch_spec is not None
    assert batch.batch_definition["data_asset_name"] == "YearTest"
    assert batch.batch_definition["batch_identifiers"] == {
        "name": "Test",
        "year": "2010",
    }
    # third batch
    batch: Batch = batch_list[2]
    assert batch.batch_spec is not None
    assert batch.batch_definition["data_asset_name"] == "YearTest"
    assert batch.batch_definition["batch_identifiers"] == {
        "name": "Test",
        "year": "2000",
    }


def test_get_batch_list_from_new_style_datasource_with_file_system_datasource_configured_assets_testing_limit_in_get_batch_list_with_batch_request(
    empty_data_context, tmp_path_factory
):
    context = empty_data_context
    base_directory = str(
        tmp_path_factory.mktemp(
            "test_get_batch_list_from_new_style_datasource_with_file_system_datasource_configured_assets_testing_limit_in_get_batch_list_with_batch_request"
        )
    )
    create_files_in_directory(
        directory=base_directory,
        file_name_list=[
            "Test_1998.csv",
            "Test_1999.csv",
            "Test_2000.csv",
            "Test_2010.csv",
            "Test_2021.csv",
        ],
        file_content_fn=lambda: "x,y,z\n1,2,3\n2,3,5",
    )

    config = yaml.load(
        f"""
    class_name: Datasource

    execution_engine:
        class_name: PandasExecutionEngine

    data_connectors:
        my_data_connector:
            class_name: ConfiguredAssetFilesystemDataConnector
            base_directory: {base_directory}
            glob_directive: "*.csv"

            default_regex:
                pattern: (.+)_(\\d.*)\\.csv
                group_names:
                    - name
                    - year
            sorters:
                - orderby: desc
                  class_name: NumericSorter
                  name: year
            assets:
                YearTest:
                    base_directory: {base_directory}
                    pattern: (.+)_(\\d.*)\\.csv
                    group_names:
                        - name
                        - year

        """,
    )
    context.add_datasource(
        "my_datasource",
        **config,
    )

    # only select files from 1999 or later
    def my_custom_batch_selector(batch_identifiers: dict) -> bool:
        return int(batch_identifiers["year"]) >= 1999

    # Use an instantiated BatchRequest object with custom filter
    batch_request: BatchRequest = BatchRequest(
        datasource_name="my_datasource",
        data_connector_name="my_data_connector",
        data_asset_name="YearTest",
        data_connector_query={"custom_filter_function": my_custom_batch_selector},
    )

    # Add the limit here in the call to get_batch_list instead of in the BatchRequest. The limit is ignored since we passed a BatchRequest via batch_request
    batch_list: List[Batch] = context.get_batch_list(
        batch_request=batch_request, limit=2
    )
    assert len(batch_list) == 4

    # first batch
    batch: Batch = batch_list[0]
    assert batch.batch_spec is not None
    assert batch.batch_definition["data_asset_name"] == "YearTest"
    assert batch.batch_definition["batch_identifiers"] == {
        "name": "Test",
        "year": "2021",
    }

    # second batch
    batch: Batch = batch_list[1]
    assert batch.batch_spec is not None
    assert batch.batch_definition["data_asset_name"] == "YearTest"
    assert batch.batch_definition["batch_identifiers"] == {
        "name": "Test",
        "year": "2010",
    }
