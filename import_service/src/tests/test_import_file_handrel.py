import json
from unittest.mock import patch

from import_service.src.handlers.import_handler import handler


def test_handler_with_valid_name(mock_event):
    with patch(
            target="import_service.src.handlers.import_handler.get_presigned_url",
            return_value="https://test.com/import?name=example.csv",
    ):
        response = handler(mock_event, None)

    expected_response = {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({"url": "https://test.com/import?name=example.csv"}),
    }

    assert response == expected_response
    assert response['statusCode'] == 200


def test_handler_with_missing_name(mock_event):
    mock_event["queryStringParameters"] = {}

    response = handler(mock_event, None)

    expected_response = {
        "statusCode": 400,
        "body": json.dumps({"message": "Missing name"}),
    }

    assert response == expected_response


def test_handler_with_exception(mock_event):
    with patch(
            target="import_service.src.handlers.import_handler.get_presigned_url",
            side_effect=Exception("Some error")
    ):
        response = handler(mock_event, None)

    expected_response = {
        "statusCode": 500,
        "headers": {
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({"message": "Some error"}),
    }

    assert response == expected_response
