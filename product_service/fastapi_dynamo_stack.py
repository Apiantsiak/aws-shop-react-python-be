from typing import cast

import aws_cdk
from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
)
from constructs import Construct


class FastApiProductsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        products_table = dynamodb.Table(
            self, 'ProductsTable',
            table_name='Products',
            removal_policy=aws_cdk.RemovalPolicy.DESTROY,
            partition_key=dynamodb.Attribute(
                name='id',
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        stocks_table = dynamodb.Table(
            self, 'StocksTable',
            table_name='Stocks',
            removal_policy=aws_cdk.RemovalPolicy.DESTROY,
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

        lambda_url = fastapi_lambda.add_function_url(
            auth_type=_lambda.FunctionUrlAuthType.NONE,
            cors=_lambda.FunctionUrlCorsOptions(
                allowed_origins=["*"],
                allowed_headers=["*"],
                allowed_methods=[_lambda.HttpMethod.ALL]
            )
        )

        aws_cdk.CfnOutput(
            self,
            "ProductServiceURl",
            value=lambda_url.url
        )
