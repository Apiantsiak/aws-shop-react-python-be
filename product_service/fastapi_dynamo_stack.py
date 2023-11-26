from typing import cast

import aws_cdk
from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
)
from constructs import Construct


class FastApiProductsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        products_table = dynamodb.Table(
            self, 'ProductsTable',
            table_name='Products',
            partition_key=dynamodb.Attribute(
                name='id',
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        stocks_table = dynamodb.Table(
            self, 'StocksTable',
            table_name='Stocks',
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
                bundling=aws_cdk.BundlingOptions(
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

        rest_api = apigw.LambdaRestApi(
            self,
            "FastApiEndpoints",
            handler=fastapi_lambda,
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=apigw.Cors.DEFAULT_HEADERS,
            ),
        )

        aws_cdk.CfnOutput(
            self,
            "ProductServiceURl",
            value=rest_api.url
        )
