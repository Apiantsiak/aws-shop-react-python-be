from typing import cast

from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    RemovalPolicy,
    BundlingOptions,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_lambda_event_sources as lm_event_src,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subs,
    aws_sqs as sqs,
)
from constructs import Construct
from .src.config import settings


class FastApiProductsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        products_table = dynamodb.Table(
            self, 'ProductsTable',
            table_name=settings.PRODUCTS_TABLE,
            removal_policy=RemovalPolicy.DESTROY,
            partition_key=dynamodb.Attribute(
                name='id',
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        stocks_table = dynamodb.Table(
            self, 'StocksTable',
            table_name=settings.STOCKS_TABLE,
            removal_policy=RemovalPolicy.DESTROY,
            partition_key=dynamodb.Attribute(
                name='product_id',
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        fastapi_lambda = _lambda.Function(
            self, 'FastApiHandler',
            runtime=cast(_lambda.Runtime, _lambda.Runtime.PYTHON_3_12),
            code=_lambda.Code.from_asset(
                path='product_service/src',
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_12.bundling_image,
                    command=[
                        "bash", "-c", "pip install -r req-app.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            ),
            handler='main.handler',
            function_name='FastApiProducts',
            environment={
                "PRODUCTS_TABLE": products_table.table_name,
                "STOCKS_TABLE": stocks_table.table_name,
            }
        )

        products_table.grant_read_write_data(fastapi_lambda)
        stocks_table.grant_read_write_data(fastapi_lambda)

        lambda_url = fastapi_lambda.add_function_url(
            auth_type=_lambda.FunctionUrlAuthType.NONE,
            cors=_lambda.FunctionUrlCorsOptions(
                allowed_origins=["*"],
                allowed_headers=["*"],
                allowed_methods=[_lambda.HttpMethod.ALL]
            )
        )

        dead_letter_queue = sqs.DeadLetterQueue(
            max_receive_count=1,
            queue=sqs.Queue(
                self,
                id="DeadLetterProductsQueue",
                retention_period=Duration.days(7)
            )
        )

        upload_queue = sqs.Queue(
            self,
            id="UploadProductsQueue",
            queue_name=settings.UPLOAD_QUEUE_NAME,
            dead_letter_queue=dead_letter_queue,
            visibility_timeout=Duration.seconds(settings.LAMBDA_TIMEOUT)
        )

        upload_event_topic = sns.Topic(
            self,
            id="UploadProductsTopic",
            display_name="Upload Products Topic"
        )

        upload_event_topic.add_subscription(
            topic_subscription=sns_subs.EmailSubscription(
                email_address=settings.SNS_EMAIL,
            )
        )

        catalog_batch_process_lambda = _lambda.Function(
            self, 'CatalogBatchProcess',
            runtime=cast(_lambda.Runtime, _lambda.Runtime.PYTHON_3_12),
            code=_lambda.Code.from_asset(
                path='product_service/src',
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_12.bundling_image,
                    command=[
                        "bash", "-c", "pip install -r req-app.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            ),
            handler='catalog_batch_process.handler',
            function_name='CatalogBatchProcessLambda',
            environment={
                "PRODUCTS_TABLE": products_table.table_name,
                "STOCKS_TABLE": stocks_table.table_name,
                "UPLOAD_TOPIC_ARN": upload_event_topic.topic_arn,
            },
            timeout=Duration.seconds(settings.LAMBDA_TIMEOUT)
        )

        catalog_batch_process_lambda.add_event_source(
            source=lm_event_src.SqsEventSource(
                queue=upload_queue,
                batch_size=5,
            )
        )
        catalog_batch_process_lambda.add_event_source(
            source=lm_event_src.SnsEventSource(
                topic=upload_event_topic
            )
        )

        upload_queue.grant_consume_messages(catalog_batch_process_lambda)

        products_table.grant_read_write_data(catalog_batch_process_lambda)
        stocks_table.grant_read_write_data(catalog_batch_process_lambda)

        upload_event_topic.grant_publish(catalog_batch_process_lambda)

        CfnOutput(
            self,
            "ProductServiceURl",
            value=lambda_url.url
        )
