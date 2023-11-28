import json

import boto3
from mypy_boto3_dynamodb import DynamoDBClient

from db_data import TABLES_DATA


def get_dynamo_client() -> DynamoDBClient:
    client = boto3.client("dynamodb")
    return client


def _fill_database(client: DynamoDBClient) -> None:
    print(json.dumps(TABLES_DATA, indent=4))
    perm = input("Do you want to insert this data y/n:  ")
    if perm == "y".strip():
        try:
            response = client.batch_write_item(RequestItems=TABLES_DATA)
        except Exception as err:
            print(err)
        else:
            print("Insertion complete successful!")
    else:
        print("Stop inserting ...")


if __name__ == '__main__':
    db_client = get_dynamo_client()
    _fill_database(db_client)
