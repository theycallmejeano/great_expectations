from tests.test_utils import get_awsathena_connection_url


def test_get_awsathena_connection_url(monkeypatch):
    monkeypatch.setenv("ATHENA_STAGING_S3", "s3://test-staging/")
    monkeypatch.setenv("ATHENA_DB_NAME", "test_db_name")
    monkeypatch.setenv("ATHENA_TEN_TRIPS_DB_NAME", "test_ten_trips_db_name")

    assert (
        get_awsathena_connection_url()
        == "awsathena+rest://@athena.us-east-1.amazonaws.com/test_db_name?s3_staging_dir=s3://test-staging/"
    )

    assert (
        get_awsathena_connection_url(db_name_env_var="ATHENA_TEN_TRIPS_DB_NAME")
        == "awsathena+rest://@athena.us-east-1.amazonaws.com/test_ten_trips_db_name?s3_staging_dir=s3://test-staging/"
    )
