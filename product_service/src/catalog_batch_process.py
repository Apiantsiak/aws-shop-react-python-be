import json
import os
from decimal import Decimal
from uuid import uuid4

import boto3
from aws_lambda_powertools.utilities.parser import BaseModel
from aws_lambda_powertools.utilities.parser import event_parser, envelopes
from aws_lambda_powertools.utilities.typing import LambdaContext
from boto3.dynamodb.types import TypeSerializer
from mypy_boto3_sns import SNSClient
from pydantic import Field

UPLOAD_TOPIC_ARN = os.environ.get("UPLOAD_TOPIC_ARN")

db_client = boto3.client("dynamodb")
sns_client: SNSClient = boto3.client("sns")


class ProductSqsRecord(BaseModel):
    count: int = Field(gt=0)
    price: Decimal
    title: str
    description: str


class NewProduct(BaseModel):
    id: str
    price: Decimal
    title: str
    description: str


class NewStock(BaseModel):
    product_id: str
    count: int = Field(gt=0)


def create_products(products: list[ProductSqsRecord]):
    try:
        db_serializer: TypeSerializer = TypeSerializer()
        pr_items = []
        st_items = []
        for product in products:
            product_id = f"{uuid4()}"
            pr_items.append(
                {
                    "Put": {
                        'TableName': "Products",
                        'Item': {
                            key: db_serializer.serialize(val) for key, val in NewProduct(
                                id=product_id, **product.dict()
                            )
                        },
                        'ConditionExpression': 'attribute_not_exists(id)',
                        "ReturnValuesOnConditionCheckFailure": "ALL_OLD",
                    }
                }
            )
            st_items.append(
                {
                    "Put": {
                        'TableName': "Stocks",
                        'Item': {
                            key: db_serializer.serialize(val) for key, val in NewStock(
                                product_id=product_id, **product.dict()
                            )
                        },
                        'ConditionExpression': 'attribute_not_exists(id)',
                        "ReturnValuesOnConditionCheckFailure": "ALL_OLD",
                    }
                }
            )
        boto3.client("dynamodb").transact_write_items(
            TransactItems=pr_items + st_items
        )
        return pr_items + st_items
    except Exception as err:
        print(err)
        raise err


@event_parser(model=ProductSqsRecord, envelope=envelopes.SqsEnvelope)
def handler(event: ProductSqsRecord, context: LambdaContext):
    try:
        uploaded_items = create_products(event)
        sns_client.publish(
            TopicArn=UPLOAD_TOPIC_ARN,
            Subject="[CATALOG BATCH] Upload products from CSV",
            Message=json.dumps(
                {
                    "Items": uploaded_items,
                    "Count": len(uploaded_items),
                    "Message": "Products were successfully uploaded from csv",
                }
            )
        )
    except Exception as err:
        uploaded_items = create_products(event)
        sns_client.publish(
            TopicArn=UPLOAD_TOPIC_ARN,
            Subject="[CATALOG BATCH] Upload products from CSV",
            Message=json.dumps(
                {
                    "Items": uploaded_items,
                    "Count": len(uploaded_items),
                    "Message": err,
                },
                indent=4,
            )
        )
        print(f"Error in Lambda handler: {err}")
        raise err
