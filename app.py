#!/usr/bin/env python3
import os

import aws_cdk as cdk

from product_service.product_service_stack import ProductServiceStack


app = cdk.App()
ProductServiceStack(
    app, "ProductServiceStack",
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION'),
    ),
)

app.synth()
