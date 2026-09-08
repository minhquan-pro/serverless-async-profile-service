import json
import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from aws_lambda_powertools import Logger, Tracer

# Globals
logger = Logger()
tracer = Tracer(service="APP")
address_table = os.getenv('TABLE_NAME')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(address_table)

@tracer.capture_method 
def list_addresses(event, context):
    logger.info(event)
    user_id = event['requestContext']['authorizer']['claims']['sub']
    logger.info(f"Retrieving addresses for user %s", user_id)

    response = table.query(
        KeyConditionExpression=Key('user_id').eq(user_id)
    )
    items = response['Items']
    # remove the user_id property since it should be transparent to the user
    for item in items:
        item.pop("user_id", None)

    logger.info(items)
    logger.info(f"Found {len(items)} address(es) for user.")
    return items

@tracer.capture_lambda_handler
def lambda_handler(event, context):
    try:
        addresses = list_addresses(event, context)
        response = {
            "statusCode": 200,
            "headers": {},
            "body": json.dumps({
                "addresses": addresses
            })
        }
        return response
    except Exception as err:
        logger.exception(err)
        raise
