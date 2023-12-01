import json
import typing as tp
from http import HTTPStatus


def config_response(
        status_code: HTTPStatus,
        body: tp.Union[list[dict[str, str]], dict[str, str]]
) -> dict:
    response = {
        "statusCode": status_code,
        "headers": {
            "Access-Control-Allow-Credentials": False,
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        },
        "body": json.dumps(body)
    }
    return response
