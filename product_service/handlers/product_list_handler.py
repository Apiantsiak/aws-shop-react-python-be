import json
from http import HTTPStatus

from constants import PRODUCTS
from utils import config_response


def get_product_list(event, context):
    try:
        print(f'request: {json.dumps(event, indent=4)}')
        response = config_response(HTTPStatus.OK, PRODUCTS)
    except Exception as err:
        return config_response(HTTPStatus.INTERNAL_SERVER_ERROR, {"message": str(err)})
    else:
        return response
