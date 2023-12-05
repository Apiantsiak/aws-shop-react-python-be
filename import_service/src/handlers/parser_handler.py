import csv
import os
from io import StringIO
from typing import List, Dict, Any
from urllib.parse import unquote_plus

import boto3
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from mypy_boto3_s3.client import S3Client

load_dotenv()

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER")
PARSED_FOLDER = os.environ.get("PARSED_FOLDER")

s3_client = boto3.client("s3")


def move_file(client: S3Client, bucket_name: str, source_key: str, destination_key: str) -> None:
    try:
        copy_params = {"Bucket": bucket_name, "CopySource": f"{bucket_name}/{source_key}", "Key": destination_key}
        client.copy_object(**copy_params)
        print(f"Object copied from {source_key} to {destination_key}")

        delete_params = {"Bucket": bucket_name, "Key": source_key}
        client.delete_object(**delete_params)
        print(f"Object deleted from {source_key}")

    except ClientError as err:
        print(f"Error: {err}")
        raise err


def parse_csv(data: bytes) -> List[Dict[str, Any]]:
    csv_file = StringIO(data.decode("utf-8"))
    reader = list(csv.DictReader(csv_file))
    return reader


def handler(event: Dict[str, Any], context: Any) -> None:
    try:
        bucket = event["Records"][0]["s3"]["bucket"]["name"]
        key = unquote_plus(event["Records"][0]["s3"]["object"]["key"])

        response = s3_client.get_object(Bucket=bucket, Key=key)
        data = response["Body"].read()

        records = parse_csv(data)

        for record in records:
            print("Record:", record)

        new_key = key.replace(UPLOAD_FOLDER, PARSED_FOLDER)
        move_file(
            client=s3_client, bucket_name=bucket, source_key=key, destination_key=new_key
        )

    except Exception as err:
        print(f"Error in Lambda handler: {err}")
        raise err
