import base64
import os

from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.api_gateway_authorizer_event import (
    APIGatewayAuthorizerTokenEvent,
    APIGatewayAuthorizerResponse,
)


@event_source(data_class=APIGatewayAuthorizerTokenEvent)
def handler(event: APIGatewayAuthorizerTokenEvent, context):
    try:
        print(event)
        auth_token = event.authorization_token.split(" ")[1]
        user, password = base64.b64decode(auth_token).decode('utf-8').split(":")

        print(user, password)

        arn = event.parsed_arn
        policy = APIGatewayAuthorizerResponse(
            principal_id=user,
            region=arn.region,
            aws_account_id=arn.aws_account_id,
            api_id=arn.api_id,
            stage=arn.stage
        )
        if password == os.getenv(user):
            policy.allow_all_routes()
        else:
            policy.deny_all_routes()
    except Exception as err:
        print(f"Error: {err}")
    else:
        return policy.asdict()
