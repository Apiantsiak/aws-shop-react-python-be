#!/usr/bin/env python3

import aws_cdk as cdk

from import_service.import_s3event_lambda_stack import ImportServiceStack
from product_service.fastapi_dynamo_stack import FastApiProductsStack
from authorization_service.authorization_lamda_stack import AuthorizationServiceStack


app = cdk.App()

FastApiProductsStack(app, construct_id="FastApiProductsServiceStack")
ImportServiceStack(app, construct_id="ImportServiceStack")
AuthorizationServiceStack(app, construct_id="AuthorizationServiceStack")

app.synth()
