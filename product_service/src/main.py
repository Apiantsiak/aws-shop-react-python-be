import json
import logging
from decimal import Decimal
from uuid import uuid4

import boto3
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
from mypy_boto3_dynamodb import DynamoDBClient
from pydantic import BaseModel, Field

app = FastAPI(title="ProductApi", version="0.1")


# handler = Mangum(app)

def handler(event, context):
    logging.info(msg=json.dumps(event, indent=4))
    asgi_handler = Mangum(app)
    response = asgi_handler(event, context)
    return response


def get_dynamo_client() -> DynamoDBClient:
    client = boto3.resource("dynamodb")
    return client


class ProductsResponse(BaseModel):
    id: str
    count: int = Field(gt=0)
    price: Decimal
    title: str
    description: str


class ProductsRequest(BaseModel):
    count: int = Field(gt=0)
    price: Decimal
    title: str
    description: str


@app.exception_handler(RequestValidationError)
def validation_exception_handler(
        request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder({"detail": exc.errors(), "body": request.path_params}),
    )


@app.get(path="/products", response_model=list[ProductsResponse])
async def products_list(
        db_client: DynamoDBClient = Depends(get_dynamo_client)
):
    product_table = db_client.Table("Products")
    stocks_table = db_client.Table("Stocks")

    products = product_table.scan().get("Items")
    stocks = stocks_table.scan().get("Items")

    stock_counts = {stock["product_id"]: stock["count"] for stock in stocks}
    for product in products:
        product_id = product["id"]
        if product_id in stock_counts:
            product["count"] = stock_counts[product_id]

    return products


@app.get(path="/products/{product_id}", response_model=ProductsResponse)
async def product_by_id(
        product_id: str = Path(example="207ac7a46e434349b55e0daef544aeb6"),
        db_client: DynamoDBClient = Depends(get_dynamo_client)
):
    product_table = db_client.Table("Products")
    stocks_table = db_client.Table("Stocks")

    product = product_table.get_item(Key={"id": product_id}).get("Item")
    stock = stocks_table.get_item(Key={"product_id": product_id}).get("Item")
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with {product_id} not found")
    product["count"] = stock["count"]

    return product


@app.post(path="/products", response_model=ProductsResponse)
async def create_product(
        response: Response,
        product_request: ProductsRequest,
        db_serializer: TypeSerializer = Depends(TypeSerializer),
):
    try:
        new_product_id = f"{uuid4().hex}"

        new_product = {
            "id": new_product_id,
            "price": product_request.price,
            "title": product_request.title,
            "description": product_request.description,
        }

        new_stock = {
            "product_id": new_product_id,
            "count": product_request.count,
        }

        queue = [
            ("Put", table, item)
            for table, item in [("Products", new_product), ("Stocks", new_stock)]
        ]

        boto3.client("dynamodb").transact_write_items(
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
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        response.body = {"details": err}
    else:
        new_product["count"] = product_request.count
        response.status_code = status.HTTP_201_CREATED
        return new_product
