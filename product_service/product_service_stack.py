from typing import cast

import aws_cdk
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigatewayv2_alpha as apigwv2,
    aws_apigatewayv2_integrations_alpha as apigwv2_integ,
)
from constructs import Construct


class ProductServiceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        product_list_lambda = _lambda.Function(
            self, 'ProductListHandler',
            runtime=cast(_lambda.Runtime, _lambda.Runtime.PYTHON_3_10),
            code=_lambda.Code.from_asset('product_service/handlers'),
            handler='product_list_handler.get_product_list',
            function_name='get_product_list',
        )

        product_id_lambda = _lambda.Function(
            self, 'ProductByIdHandler',
            runtime=cast(_lambda.Runtime, _lambda.Runtime.PYTHON_3_10),
            code=_lambda.Code.from_asset('product_service/handlers'),
            handler='product_by_id_handler.get_product_by_id',
            function_name='get_product_by_id',
        )

        http_apigw = apigwv2.HttpApi(
            self, "ProductApiGateway",
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_headers=["Authorization"],
                allow_methods=[apigwv2.CorsHttpMethod.ANY],
                allow_origins=["*"],
            )
        )

        http_apigw.add_routes(
            path="/products",
            methods=[apigwv2.HttpMethod.GET],
            integration=apigwv2_integ.HttpLambdaIntegration(
                "ProductListIntegration", product_list_lambda
            )
        )

        http_apigw.add_routes(
            path="/products/{productId}",
            methods=[apigwv2.HttpMethod.GET],
            integration=apigwv2_integ.HttpLambdaIntegration(
                "ProductByIdIntegration", product_id_lambda
            )
        )

        aws_cdk.CfnOutput(
            self,
            "ProductServiceURl",
            value=http_apigw.url
        )
