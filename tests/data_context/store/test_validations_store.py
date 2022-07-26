import datetime
from unittest import mock

import boto3
import pytest
from freezegun import freeze_time
from moto import mock_s3

import tests.test_utils as test_utils
from great_expectations.core import ExpectationSuiteValidationResult
from great_expectations.core.expectation_validation_result import (
    ExpectationSuiteValidationResult,
)
from great_expectations.data_context.store import ValidationsStore
from great_expectations.data_context.types.resource_identifiers import (
    ExpectationSuiteIdentifier,
    ValidationResultIdentifier,
)
from great_expectations.util import gen_directory_tree_str
from tests.core.usage_statistics.util import (
    usage_stats_exceptions_exist,
    usage_stats_invalid_messages_exist,
)


@freeze_time("09/26/2019 13:42:41")
@mock_s3
@pytest.mark.filterwarnings(
    "ignore:String run_ids are deprecated*:DeprecationWarning:great_expectations.data_context.types.resource_identifiers"
)
def test_ValidationsStore_with_TupleS3StoreBackend():
    bucket = "test_validation_store_bucket"
    prefix = "test/prefix"

    # create a bucket in Moto's mock AWS environment
    conn = boto3.resource("s3", region_name="us-east-1")
    conn.create_bucket(Bucket=bucket)

    # First, demonstrate that we pick up default configuration including from an S3TupleS3StoreBackend
    my_store = ValidationsStore(
        store_backend={
            "class_name": "TupleS3StoreBackend",
            "bucket": bucket,
            "prefix": prefix,
        }
    )

    with pytest.raises(TypeError):
        my_store.get("not_a_ValidationResultIdentifier")

    ns_1 = ValidationResultIdentifier(
        expectation_suite_identifier=ExpectationSuiteIdentifier(
            expectation_suite_name="asset.quarantine",
        ),
        run_id="20191007T151224.1234Z_prod_100",
        batch_identifier="batch_id",
    )
    my_store.set(ns_1, ExpectationSuiteValidationResult(success=True))
    assert my_store.get(ns_1) == ExpectationSuiteValidationResult(
        success=True, statistics={}, results=[]
    )

    ns_2 = ValidationResultIdentifier(
        expectation_suite_identifier=ExpectationSuiteIdentifier(
            expectation_suite_name="asset.quarantine",
        ),
        run_id="20191007T151224.1234Z_prod_200",
        batch_identifier="batch_id",
    )

    my_store.set(ns_2, ExpectationSuiteValidationResult(success=False))
    assert my_store.get(ns_2) == ExpectationSuiteValidationResult(
        success=False, statistics={}, results=[]
    )

    # Verify that internals are working as expected, including the default filepath
    assert {
        s3_object_info["Key"]
        for s3_object_info in boto3.client("s3").list_objects_v2(
            Bucket=bucket, Prefix=prefix
        )["Contents"]
    } == {
        "test/prefix/.ge_store_backend_id",
        "test/prefix/asset/quarantine/20191007T151224.1234Z_prod_100/20190926T134241.000000Z/batch_id.json",
        "test/prefix/asset/quarantine/20191007T151224.1234Z_prod_200/20190926T134241.000000Z/batch_id.json",
    }

    print(my_store.list_keys())
    assert set(my_store.list_keys()) == {
        ns_1,
        ns_2,
    }

    """
    What does this test and why?
    A Store should be able to report it's store_backend_id
    which is set when the StoreBackend is instantiated.
    """
    # Check that store_backend_id exists can be read
    assert my_store.store_backend_id is not None
    # Check that store_backend_id is a valid UUID
    assert test_utils.validate_uuid4(my_store.store_backend_id)


@freeze_time("09/26/2019 13:42:41")
def test_ValidationsStore_with_InMemoryStoreBackend():
    my_store = ValidationsStore(
        store_backend={
            "module_name": "great_expectations.data_context.store",
            "class_name": "InMemoryStoreBackend",
        }
    )

    with pytest.raises(TypeError):
        my_store.get("not_a_ValidationResultIdentifier")

    ns_1 = ValidationResultIdentifier.from_tuple(
        (
            "a",
            "b",
            "c",
            "quarantine",
            datetime.datetime.now(datetime.timezone.utc),
            "prod-100",
        )
    )
    my_store.set(ns_1, ExpectationSuiteValidationResult(success=True))
    assert my_store.get(ns_1) == ExpectationSuiteValidationResult(
        success=True, statistics={}, results=[]
    )

    ns_2 = ValidationResultIdentifier.from_tuple(
        (
            "a",
            "b",
            "c",
            "quarantine",
            datetime.datetime.now(datetime.timezone.utc),
            "prod-200",
        )
    )
    my_store.set(ns_2, ExpectationSuiteValidationResult(success=False))
    assert my_store.get(ns_2) == ExpectationSuiteValidationResult(
        success=False, statistics={}, results=[]
    )
    assert set(my_store.list_keys()) == {
        ns_1,
        ns_2,
    }
    """
    What does this test and why?
    A Store should be able to report it's store_backend_id
    which is set when the StoreBackend is instantiated.
    """
    # Check that store_backend_id exists can be read
    assert my_store.store_backend_id is not None
    # Check that store_backend_id is a valid UUID
    assert test_utils.validate_uuid4(my_store.store_backend_id)


@pytest.mark.integration
@freeze_time("09/26/2019 13:42:41")
@pytest.mark.filterwarnings(
    "ignore:String run_ids are deprecated*:DeprecationWarning:great_expectations.data_context.types.resource_identifiers"
)
def test_ValidationsStore_with_TupleFileSystemStoreBackend(tmp_path_factory):
    full_test_dir = tmp_path_factory.mktemp(
        "test_ValidationResultStore_with_TupleFileSystemStoreBackend__dir"
    )
    test_dir = full_test_dir.parts[-1]
    path = str(full_test_dir)

    my_store = ValidationsStore(
        store_backend={
            "module_name": "great_expectations.data_context.store",
            "class_name": "TupleFilesystemStoreBackend",
            "base_directory": "my_store/",
        },
        runtime_environment={"root_directory": path},
    )

    with pytest.raises(TypeError):
        my_store.get("not_a_ValidationResultIdentifier")

    ns_1 = ValidationResultIdentifier(
        expectation_suite_identifier=ExpectationSuiteIdentifier("asset.quarantine"),
        run_id="prod-100",
        batch_identifier="batch_id",
    )
    my_store.set(ns_1, ExpectationSuiteValidationResult(success=True))
    assert my_store.get(ns_1) == ExpectationSuiteValidationResult(
        success=True, statistics={}, results=[]
    )

    ns_2 = ValidationResultIdentifier.from_tuple(
        (
            "asset",
            "quarantine",
            "prod-20",
            datetime.datetime.now(datetime.timezone.utc),
            "batch_id",
        )
    )
    my_store.set(ns_2, ExpectationSuiteValidationResult(success=False))
    assert my_store.get(ns_2) == ExpectationSuiteValidationResult(
        success=False, statistics={}, results=[]
    )

    assert set(my_store.list_keys()) == {
        ns_1,
        ns_2,
    }

    assert (
        gen_directory_tree_str(path)
        == f"""\
{test_dir}/
    my_store/
        .ge_store_backend_id
        asset/
            quarantine/
                prod-100/
                    20190926T134241.000000Z/
                        batch_id.json
                prod-20/
                    20190926T134241.000000Z/
                        batch_id.json
"""
    )

    """
    What does this test and why?
    A Store should be able to report it's store_backend_id
    which is set when the StoreBackend is instantiated.
    """
    # Check that store_backend_id exists can be read
    assert my_store.store_backend_id is not None
    # Check that store_backend_id is a valid UUID
    assert test_utils.validate_uuid4(my_store.store_backend_id)

    # Check that another store with the same configuration shares the same store_backend_id
    my_store_duplicate = ValidationsStore(
        store_backend={
            "module_name": "great_expectations.data_context.store",
            "class_name": "TupleFilesystemStoreBackend",
            "base_directory": "my_store/",
        },
        runtime_environment={"root_directory": path},
    )
    assert my_store.store_backend_id == my_store_duplicate.store_backend_id


@pytest.mark.filterwarnings(
    "ignore:String run_ids are deprecated*:DeprecationWarning:great_expectations.data_context.types.resource_identifiers"
)
def test_ValidationsStore_with_DatabaseStoreBackend(sa):
    # Use sqlite so we don't require postgres for this test.
    connection_kwargs = {"drivername": "sqlite"}

    # First, demonstrate that we pick up default configuration
    my_store = ValidationsStore(
        store_backend={
            "class_name": "DatabaseStoreBackend",
            "credentials": connection_kwargs,
        }
    )

    with pytest.raises(TypeError):
        my_store.get("not_a_ValidationResultIdentifier")

    ns_1 = ValidationResultIdentifier(
        expectation_suite_identifier=ExpectationSuiteIdentifier(
            expectation_suite_name="asset.quarantine",
        ),
        run_id="20191007T151224.1234Z_prod_100",
        batch_identifier="batch_id",
    )
    my_store.set(ns_1, ExpectationSuiteValidationResult(success=True))
    assert my_store.get(ns_1) == ExpectationSuiteValidationResult(
        success=True, statistics={}, results=[]
    )

    ns_2 = ValidationResultIdentifier(
        expectation_suite_identifier=ExpectationSuiteIdentifier(
            expectation_suite_name="asset.quarantine",
        ),
        run_id="20191007T151224.1234Z_prod_200",
        batch_identifier="batch_id",
    )

    my_store.set(ns_2, ExpectationSuiteValidationResult(success=False))
    assert my_store.get(ns_2) == ExpectationSuiteValidationResult(
        success=False, statistics={}, results=[]
    )

    assert set(my_store.list_keys()) == {
        ns_1,
        ns_2,
    }

    """
    What does this test and why?
    A Store should be able to report it's store_backend_id
    which is set when the StoreBackend is instantiated.
    """
    # Check that store_backend_id exists can be read
    assert my_store.store_backend_id is not None
    # Check that store_backend_id is a valid UUID
    assert test_utils.validate_uuid4(my_store.store_backend_id)


@mock.patch(
    "great_expectations.core.usage_statistics.usage_statistics.UsageStatisticsHandler.emit"
)
@pytest.mark.filterwarnings(
    "ignore:String run_ids are deprecated*:DeprecationWarning:great_expectations.data_context.types.resource_identifiers"
)
def test_instantiation_with_test_yaml_config(
    mock_emit, caplog, empty_data_context_stats_enabled
):
    empty_data_context_stats_enabled.test_yaml_config(
        yaml_config="""
module_name: great_expectations.data_context.store.validations_store
class_name: ValidationsStore
store_backend:
    class_name: TupleFilesystemStoreBackend
    base_directory: uncommitted/validations/
"""
    )
    assert mock_emit.call_count == 1
    # Substitute current anonymized name since it changes for each run
    anonymized_name = mock_emit.call_args_list[0][0][0]["event_payload"][
        "anonymized_name"
    ]
    assert mock_emit.call_args_list == [
        mock.call(
            {
                "event": "data_context.test_yaml_config",
                "event_payload": {
                    "anonymized_name": anonymized_name,
                    "parent_class": "ValidationsStore",
                    "anonymized_store_backend": {
                        "parent_class": "TupleFilesystemStoreBackend"
                    },
                },
                "success": True,
            }
        ),
    ]

    # Confirm that logs do not contain any exceptions or invalid messages
    assert not usage_stats_exceptions_exist(messages=caplog.messages)
    assert not usage_stats_invalid_messages_exist(messages=caplog.messages)
