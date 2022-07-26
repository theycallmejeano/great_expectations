from unittest import mock

import pytest
from ruamel import yaml

from great_expectations.data_context import BaseDataContext, DataContext
from great_expectations.data_context.store import GeCloudStoreBackend
from great_expectations.data_context.types.base import DataContextConfig
from great_expectations.exceptions import DataContextError, GeCloudError


@pytest.fixture
def ge_cloud_data_context_config(
    ge_cloud_runtime_base_url,
    ge_cloud_runtime_organization_id,
    ge_cloud_runtime_access_token,
):
    """
    This fixture is used to replicate a response retrieved from a GE Cloud API request.
    The resulting data is packaged into a DataContextConfig.

    Please see DataContext._retrieve_data_context_config_from_ge_cloud for more details.
    """
    DEFAULT_GE_CLOUD_DATA_CONTEXT_CONFIG = f"""
    datasources:
      default_spark_datasource:
        execution_engine:
          module_name: great_expectations.execution_engine
          class_name: SparkDFExecutionEngine
        module_name: great_expectations.datasource
        class_name: Datasource
        data_connectors:
          default_runtime_data_connector:
            class_name: RuntimeDataConnector
            batch_identifiers:
                - timestamp
      default_pandas_datasource:
          execution_engine:
            module_name: great_expectations.execution_engine
            class_name: PandasExecutionEngine
          module_name: great_expectations.datasource
          class_name: Datasource
          data_connectors:
            default_runtime_data_connector:
              class_name: RuntimeDataConnector
              batch_identifiers:
                - timestamp

    stores:
      default_evaluation_parameter_store:
        class_name: EvaluationParameterStore

      default_expectations_store:
        class_name: ExpectationsStore
        store_backend:
          class_name: GeCloudStoreBackend
          ge_cloud_base_url: {ge_cloud_runtime_base_url}
          ge_cloud_resource_type: expectation_suite
          ge_cloud_credentials:
            access_token: {ge_cloud_runtime_access_token}
            organization_id: {ge_cloud_runtime_organization_id}
          suppress_store_backend_id: True

      default_validations_store:
        class_name: ValidationsStore
        store_backend:
          class_name: GeCloudStoreBackend
          ge_cloud_base_url: {ge_cloud_runtime_base_url}
          ge_cloud_resource_type: suite_validation_result
          ge_cloud_credentials:
            access_token: {ge_cloud_runtime_access_token}
            organization_id: {ge_cloud_runtime_organization_id}
          suppress_store_backend_id: True

      default_checkpoint_store:
        class_name: CheckpointStore
        store_backend:
          class_name: GeCloudStoreBackend
          ge_cloud_base_url: {ge_cloud_runtime_base_url}
          ge_cloud_resource_type: contract
          ge_cloud_credentials:
            access_token: {ge_cloud_runtime_access_token}
            organization_id: {ge_cloud_runtime_organization_id}
          suppress_store_backend_id: True

    evaluation_parameter_store_name: default_evaluation_parameter_store
    expectations_store_name: default_expectations_store
    validations_store_name: default_validations_store
    checkpoint_store_name: default_checkpoint_store

    data_docs_sites:
      default_site:
        class_name: SiteBuilder
        show_how_to_buttons: true
        store_backend:
          class_name: GeCloudStoreBackend
          ge_cloud_base_url: {ge_cloud_runtime_base_url}
          ge_cloud_resource_type: rendered_data_doc
          ge_cloud_credentials:
            access_token: {ge_cloud_runtime_access_token}
            organization_id: {ge_cloud_runtime_organization_id}
          suppress_store_backend_id: True
        site_index_builder:
          class_name: DefaultSiteIndexBuilder
        site_section_builders:
          profiling: None

    anonymous_usage_statistics:
      enabled: true
      usage_statistics_url: https://dev.stats.greatexpectations.io/great_expectations/v1/usage_statistics
      data_context_id: {ge_cloud_data_context_config}
    """
    config = yaml.load(DEFAULT_GE_CLOUD_DATA_CONTEXT_CONFIG)
    return DataContextConfig(**config)


@pytest.mark.cloud
def test_data_context_ge_cloud_mode_with_incomplete_cloud_config_should_throw_error():
    # Don't want to make a real request in a unit test so we simply patch the config fixture
    with mock.patch(
        "great_expectations.data_context.DataContext._get_ge_cloud_config_dict",
        return_value={"base_url": None, "organization_id": None, "access_token": None},
    ):
        with pytest.raises(DataContextError):
            DataContext(context_root_dir="/my/context/root/dir", ge_cloud_mode=True)


@pytest.mark.cloud
@mock.patch("requests.get")
def test_data_context_ge_cloud_mode_makes_successful_request_to_cloud_api(
    mock_request,
    ge_cloud_runtime_base_url,
    ge_cloud_runtime_organization_id,
    ge_cloud_runtime_access_token,
):
    # Ensure that the request goes through
    mock_request.return_value.status_code = 200
    try:
        DataContext(
            ge_cloud_mode=True,
            ge_cloud_base_url=ge_cloud_runtime_base_url,
            ge_cloud_organization_id=ge_cloud_runtime_organization_id,
            ge_cloud_access_token=ge_cloud_runtime_access_token,
        )
    except:  # Not concerned with constructor output (only evaluating interaction with requests during __init__)
        pass

    called_with_url = f"{ge_cloud_runtime_base_url}/organizations/{ge_cloud_runtime_organization_id}/data-context-configuration"
    called_with_header = {
        "headers": {
            "Content-Type": "application/vnd.api+json",
            "Authorization": f"Bearer {ge_cloud_runtime_access_token}",
        }
    }

    # Only ever called once with the endpoint URL and auth token as args
    mock_request.assert_called_once()
    assert mock_request.call_args[0][0] == called_with_url
    assert mock_request.call_args[1] == called_with_header


@pytest.mark.cloud
@mock.patch("requests.get")
def test_data_context_ge_cloud_mode_with_bad_request_to_cloud_api_should_throw_error(
    mock_request,
    ge_cloud_runtime_base_url,
    ge_cloud_runtime_organization_id,
    ge_cloud_runtime_access_token,
):
    # Ensure that the request fails
    mock_request.return_value.status_code = 401

    with pytest.raises(GeCloudError):
        DataContext(
            ge_cloud_mode=True,
            ge_cloud_base_url=ge_cloud_runtime_base_url,
            ge_cloud_organization_id=ge_cloud_runtime_organization_id,
            ge_cloud_access_token=ge_cloud_runtime_access_token,
        )


@pytest.mark.cloud
@pytest.mark.unit
@mock.patch("requests.get")
def test_data_context_in_cloud_mode_passes_base_url_to_store_backend(
    mock_request,
    ge_cloud_base_url,
    empty_cloud_data_context_custom_base_url,
    ge_cloud_runtime_organization_id,
    ge_cloud_runtime_access_token,
):

    custom_base_url: str = "https://some_url.org"
    # Ensure that the request goes through
    mock_request.return_value.status_code = 200

    context = empty_cloud_data_context_custom_base_url

    # Assertions that the context fixture is set up properly
    assert not context.ge_cloud_config.base_url == GeCloudStoreBackend.DEFAULT_BASE_URL
    assert not context.ge_cloud_config.base_url == ge_cloud_base_url
    assert (
        not context.ge_cloud_config.base_url == "https://app.test.greatexpectations.io"
    )

    # The DatasourceStore should not have the default base_url or commonly used test base urls
    assert (
        not context._datasource_store.store_backend.config["ge_cloud_base_url"]
        == GeCloudStoreBackend.DEFAULT_BASE_URL
    )
    assert (
        not context._datasource_store.store_backend.config["ge_cloud_base_url"]
        == ge_cloud_base_url
    )
    assert (
        not context._datasource_store.store_backend.config["ge_cloud_base_url"]
        == "https://app.test.greatexpectations.io"
    )

    # The DatasourceStore should have the custom base url set
    assert (
        context._datasource_store.store_backend.config["ge_cloud_base_url"]
        == custom_base_url
    )
