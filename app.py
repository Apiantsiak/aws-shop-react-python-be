#!/usr/bin/env python3

import aws_cdk as cdk

from import_service.import_s3event_lambda_stack import ImportServiceStack
from product_service.fastapi_dynamo_stack import FastApiProductsStack


app = cdk.App()

FastApiProductsStack(app, construct_id="FastApiProductsServiceStack")
ImportServiceStack(app, construct_id="ImportServiceStack")

app.synth()
