import os
from moto import mock_s3
import boto3
import pytest


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture(scope="function")
def s3(aws_credentials):
    with mock_s3():
        yield boto3.client("s3", region_name="us-east-1")


@pytest.fixture()
def mock_event():
    return {
        "queryStringParameters": {
            "name": "example.csv"
        }
    }


@pytest.fixture
def s3_event():
    return {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "example-bucket"},
                    "object": {"key": "example.csv"}
                }
            }
        ]
    }