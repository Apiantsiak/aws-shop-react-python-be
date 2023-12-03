import json
import os
from dotenv import load_dotenv, find_dotenv
from typing import Dict, Any

import boto3
from botocore.exceptions import ClientError
from mypy_boto3_s3.client import S3Client

load_dotenv(find_dotenv(".env"))

BUCKET = os.getenv("UPLOAD_BUCKET")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")
EXPIRATION_SECONDS = int(os.getenv("EXPIRATION_SECONDS"))


def get_presigned_url(key: str) -> str:
    try:
        s3_client: S3Client = boto3.client("s3")

        response = s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={"Bucket": BUCKET, "Key": key},
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
        upload_url = get_presigned_url(key)

        return {
            "statusCode": 200,
            "body": json.dumps({"uploadUrl": upload_url}),
        }
    except Exception as err:
        print(f"Error in Lambda handler: {err}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": f"{err}"}),
        }
