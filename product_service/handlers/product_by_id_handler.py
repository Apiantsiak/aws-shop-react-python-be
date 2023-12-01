import json
from http import HTTPStatus

from constants import PRODUCTS
from utils import config_response


def get_product_by_id(event, context):
    try:
        print(f'request: {json.dumps(event, indent=4)}')
        event_product_id = event["pathParameters"]["productId"]
        product = [pr for pr in PRODUCTS if pr["id"] == int(event_product_id)]
        if not product:
            response = config_response(
                HTTPStatus.NOT_FOUND, {
                    "message": f"Product with id {event_product_id} not found"
                }
            )
            return response
        response = config_response(HTTPStatus.OK, product)
    except Exception as err:
        return config_response(HTTPStatus.INTERNAL_SERVER_ERROR, {"message": str(err)})
    else:
        return response
