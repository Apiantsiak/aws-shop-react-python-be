import json
import os
from typing import Dict, Any

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv, find_dotenv
from mypy_boto3_s3.client import S3Client

load_dotenv(find_dotenv(".env"))

BUCKET = os.getenv("UPLOAD_BUCKET")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")
EXPIRATION_SECONDS = int(os.getenv("EXPIRATION_SECONDS"))

s3_client = boto3.client("s3")


def get_presigned_url(client: S3Client, key: str) -> str:
    try:
        response = client.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': BUCKET,
                'Key': key,
                "ContentType": "text/csv"
            },
            ExpiresIn=EXPIRATION_SECONDS,
        )
    except ClientError as err:
        print(f"Error generating presigned URL: {err}")
        raise err
    else:
        return response


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        name = event.get("queryStringParameters", {}).get("name")
        if not name:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Missing name"}),
            }

        key = f"{UPLOAD_FOLDER}/{name}"
        upload_url = get_presigned_url(client=s3_client, key=key)

    except Exception as err:
        print(f"Error in Lambda handler: {err}")
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"message": f"{err}"}),
        }
    else:
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"url": upload_url}),
        }
