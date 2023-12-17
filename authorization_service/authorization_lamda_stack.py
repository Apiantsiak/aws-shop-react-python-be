from typing import cast

from aws_cdk import (
    Stack,
    BundlingOptions,
    aws_lambda as _lambda,
    aws_iam as iam
)
from constructs import Construct
from .src.config import settings


class AuthorizationServiceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        authorization_lambda = _lambda.Function(
            self,
            id='TokenAuthLambda',
            runtime=cast(_lambda.Runtime, _lambda.Runtime.PYTHON_3_12),
            code=_lambda.Code.from_asset(
                path='authorization_service/src',
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_12.bundling_image,
                    command=[
                        "bash", "-c", "pip install -r req-app.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            ),
            handler='basic_authorizer.handler',
            function_name='basic_token_authorizer',
            environment={
                "Apiantsiak": settings.Apiantsiak,
            }
        )

        authorization_lambda.grant_invoke(iam.ServicePrincipal("apigateway.amazonaws.com"))
