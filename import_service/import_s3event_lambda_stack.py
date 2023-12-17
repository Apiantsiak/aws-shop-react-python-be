from typing import cast

from aws_cdk import (
    Stack,
    CfnOutput,
    RemovalPolicy,
    BundlingOptions,
    aws_s3 as s3,
    aws_sqs as sqs,
    aws_lambda as _lambda,
    aws_lambda_event_sources,
    aws_apigateway as apigw,
)
from constructs import Construct

from .src.config import settings


class ImportServiceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        s3_bucket = s3.Bucket(
            self,
            id="ImportCsvBucket",
            bucket_name=settings.UPLOAD_BUCKET,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            cors=[
                s3.CorsRule(
                    allowed_methods=[
                        s3.HttpMethods.PUT,
                        s3.HttpMethods.POST,
                        s3.HttpMethods.GET,
                        s3.HttpMethods.DELETE,
                        s3.HttpMethods.HEAD,
                    ],
                    allowed_origins=["*"],
                    allowed_headers=["*"],
                )
            ],
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        import_file_lambda = _lambda.Function(
            self,
            id='ImportFile',
            runtime=cast(_lambda.Runtime, _lambda.Runtime.PYTHON_3_12),
            code=_lambda.Code.from_asset(
                path='import_service/src',
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_12.bundling_image,
                    command=[
                        "bash", "-c", "pip install -r req-app.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            ),
            handler='import_handler.handler',
            function_name='import_file',
            environment={
                "UPLOAD_BUCKET": s3_bucket.bucket_name,
                "UPLOAD_FOLDER": settings.UPLOAD_FOLDER,
                "EXPIRATION_SECONDS": f"{settings.EXPIRATION_SECONDS}",
            }
        )

        s3_bucket.grant_put(import_file_lambda)

        rest_api = apigw.RestApi(
            self,
            id="ImportRestApiGateway",
            rest_api_name="ImportServiceApi",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=apigw.Cors.DEFAULT_HEADERS,
            ),
            deploy_options=apigw.StageOptions(
                stage_name="dev",
            )
        )

        import_route_response = apigw.Model(
            self,
            id="ImportRouteResponseModel",
            rest_api=rest_api,
            schema={
                "schema": apigw.JsonSchemaVersion.DRAFT4,
                "type": apigw.JsonSchemaType.STRING,
            },
            description="Returns Pre-Signed URL to upload CSV",
            content_type="application/json",
        )

        rest_api_import_route = rest_api.root.add_resource(path_part="import")
        rest_api_import_route.add_method(
            http_method="GET",
            integration=apigw.LambdaIntegration(
                handler=import_file_lambda
            ),
            method_responses=[
                {
                    "statusCode": "200",
                    "responseModels": {"application/json": import_route_response},
                },
                {
                    "statusCode": "500",
                    "responseModels": {"application/json": apigw.Model.ERROR_MODEL},
                },
            ],
            request_parameters={
                "method.request.querystring.name": True,
            },
            request_validator_options=apigw.RequestValidatorOptions(
                validate_request_parameters=True,
            ),
        )

        upload_queue = sqs.Queue.from_queue_arn(
            self,
            id="UploadProductsQueue",
            queue_arn=settings.SQS_UPLOAD_ARN,
        )

        import_file_parse_lambda = _lambda.Function(
            self,
            id='ImportFileParser',
            runtime=cast(_lambda.Runtime, _lambda.Runtime.PYTHON_3_12),
            code=_lambda.Code.from_asset(
                path='import_service/src',
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_12.bundling_image,
                    command=[
                        "bash", "-c", "pip install -r req-app.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            ),
            handler='parser_handler.handler',
            function_name='import_file_parser',
            environment={
                "UPLOAD_BUCKET": s3_bucket.bucket_name,
                "UPLOAD_FOLDER": settings.UPLOAD_FOLDER,
                "PARSED_FOLDER": settings.PARSED_FOLDER,
                "UPLOAD_QUEUE_NAME": settings.UPLOAD_QUEUE_NAME,
            }
        )

        import_file_parse_lambda.add_event_source(
            source=aws_lambda_event_sources.S3EventSource(
                bucket=s3_bucket,
                events=[s3.EventType.OBJECT_CREATED],
                filters=[s3.NotificationKeyFilter(prefix=settings.UPLOAD_FOLDER, suffix=".csv")],
            )
        )

        upload_queue.grant_send_messages(import_file_parse_lambda)
        s3_bucket.grant_read_write(import_file_parse_lambda)

        CfnOutput(
            self,
            id="ImportServiceURL",
            value=rest_api.url
        )
