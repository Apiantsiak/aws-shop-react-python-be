from uuid import uuid4
from typing import Optional

import boto3
from fastapi import FastAPI, HTTPException, Depends, Path
from mangum import Mangum
from mypy_boto3_dynamodb import DynamoDBClient
from pydantic import BaseModel, Field

app = FastAPI(
    title="ProductApi",
    version="0.1",
    root_path="/prod/"
)
handler = Mangum(app)


def get_dynamo_client() -> DynamoDBClient:
    client = boto3.resource("dynamodb")
    return client


class ProductsResponse(BaseModel):
    id: str
    count: int = Field(gt=0)
    price: float = Field(gt=0)
    title: str
    description: str


class ProductsRequest(BaseModel):
    id: Optional[str] = None
    count: int = Field(gt=0)
    price: float = Field(gt=0)
    title: str
    description: str


@app.get("/products", response_model=list[ProductsResponse])
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


@app.get("/products/{product_id}", response_model=ProductsResponse)
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


@app.post("/products", response_model=ProductsResponse)
async def create_product(
        product_request: ProductsRequest,
        db_client: DynamoDBClient = Depends(get_dynamo_client),
):
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
    product_table = db_client.Table("Products")
    stocks_table = db_client.Table("Stocks")

    product_table.put_item(Item=new_product)
    stocks_table.put_item(Item=new_stock)

    new_product["count"] = new_stock["count"]

    return product_request
