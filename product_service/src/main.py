import json
import logging
from uuid import uuid4

from boto3.dynamodb.types import TypeSerializer
from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    Path,
    Response,
    status,
    Request
)
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from mangum import Mangum
from mypy_boto3_dynamodb import DynamoDBClient, ServiceResource

from db.db_config import get_dynamo_client, get_dynamo_resource
from entities import ProductResponse, ProductRequest, NewProduct, NewStock

app = FastAPI(title="ProductApi", version="0.1.2")


def handler(event, context):
    logging.info(msg=json.dumps(event, indent=4))
    asgi_handler = Mangum(app)
    response = asgi_handler(event, context)
    return response


@app.exception_handler(RequestValidationError)
def validation_exception_handler(
        request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder({"detail": exc.errors(), "body": request.path_params}),
    )


@app.get(path="/products", response_model=list[ProductResponse])
async def products_list(
        db_resource: ServiceResource = Depends(get_dynamo_resource)
):
    product_table = db_resource.Table("Products")
    stocks_table = db_resource.Table("Stocks")

    products = product_table.scan().get("Items")
    stocks = stocks_table.scan().get("Items")

    stock_counts = {stock["product_id"]: stock["count"] for stock in stocks}
    for product in products:
        product_id = product["id"]
        if product_id in stock_counts:
            product["count"] = stock_counts[product_id]

    return products


@app.get(path="/products/{product_id}", response_model=ProductResponse)
async def product_by_id(
        product_id: str = Path(example="655dac49-233f-4133-83c1-310adb1987cf"),
        db_resource: ServiceResource = Depends(get_dynamo_resource)
):
    product_table = db_resource.Table("Products")
    stocks_table = db_resource.Table("Stocks")

    product = product_table.get_item(Key={"id": product_id}).get("Item")
    stock = stocks_table.get_item(Key={"product_id": product_id}).get("Item")
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with {product_id} not found"
        )

    product["count"] = stock["count"]

    return product


@app.post(path="/products", response_model=ProductResponse)
async def create_product(
        response: Response,
        product_request: ProductRequest,
        db_serializer: TypeSerializer = Depends(TypeSerializer),
        db_client: DynamoDBClient = Depends(get_dynamo_client),
):
    try:
        new_product_id = f"{uuid4()}"
        product_response = {"id": new_product_id, **product_request.model_dump()}

        new_product = NewProduct(id=new_product_id, **product_request.model_dump())
        new_stock = NewStock(product_id=new_product_id, **product_request.model_dump())

        queue = [
            ("Put", table, item)
            for table, item in [
                ("Products", new_product.model_dump()),
                ("Stocks", new_stock.model_dump())
            ]
        ]

        db_client.transact_write_items(
            TransactItems=[
                {
                    method: {
                        'TableName': table,
                        'Item': {
                            key: db_serializer.serialize(value)
                            for key, value in item.items()
                        },
                        'ConditionExpression': 'attribute_not_exists(id)',
                        "ReturnValuesOnConditionCheckFailure": "ALL_OLD",
                    }
                } for method, table, item in queue
            ]
        )

    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{err}")
    else:
        response.status_code = status.HTTP_201_CREATED
        return product_response
