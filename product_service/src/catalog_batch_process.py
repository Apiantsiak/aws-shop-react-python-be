import json
import os
from uuid import uuid4

import boto3
from aws_lambda_powertools.utilities.parser import event_parser, envelopes
from aws_lambda_powertools.utilities.typing import LambdaContext
from boto3.dynamodb.types import TypeSerializer
from mypy_boto3_sns import SNSClient

from entities import ProductRequest, NewProduct, NewStock

UPLOAD_TOPIC_ARN = os.environ.get("UPLOAD_TOPIC_ARN")

db_client = boto3.client("dynamodb")
sns_client: SNSClient = boto3.client("sns")


def create_products(products: list[ProductRequest]):
    try:
        db_serializer: TypeSerializer = TypeSerializer()

        pr_items = []
        st_items = []
        for product in products:
            new_product_id = f"{uuid4()}"
            pr_items.append(
                {
                    "Put": {
                        'TableName': "Products",
                        'Item': {
                            key: db_serializer.serialize(val) for key, val in NewProduct(
                                id=new_product_id, **product.model_dump()
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
                                product_id=new_product_id, **product.model_dump()
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
        return pr_items, st_items
    except Exception as err:
        print(err)
        raise err


@event_parser(model=ProductRequest, envelope=envelopes.SqsEnvelope)
def handler(event: list[ProductRequest], context: LambdaContext):
    try:
        print(event)
        uploaded_products, uploaded_stocks = create_products(event)
        sns_client.publish(
            TopicArn=UPLOAD_TOPIC_ARN,
            Subject="[CATALOG BATCH] Upload products from CSV",
            Message=json.dumps(
                {
                    "Products": uploaded_products,
                    "Stocks": uploaded_stocks,
                    "Count": len(uploaded_products + uploaded_stocks),
                    "Message": "Products were successfully uploaded from CSV!",
                },
                indent=4,
            )
        )
    except Exception as err:
        sns_client.publish(
            TopicArn=UPLOAD_TOPIC_ARN,
            Subject="[CATALOG BATCH] Upload products from CSV",
            Message=json.dumps(
                {
                    "Message": "Upload from CSV is failed!",
                    "Error": f"{err}",
                },
                indent=4,
            )
        )
        print(f"Error in Lambda handler: {err}")
        raise err
