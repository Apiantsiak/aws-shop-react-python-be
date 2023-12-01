#!/usr/bin/env python3
import os

import aws_cdk as cdk

from product_service.product_service_stack import ProductServiceStack
from product_service.fastapi_dynamo_stack import FastApiProductsStack

app = cdk.App()
ProductServiceStack(app, "ProductServiceStack")
FastApiProductsStack(app, "FastApiProductsServiceStack")

app.synth()
