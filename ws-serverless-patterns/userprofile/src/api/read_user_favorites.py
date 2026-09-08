import json
import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from aws_lambda_powertools import Logger, Tracer

# Globals
logger = Logger()
tracer = Tracer(service="APP")
favorites_table = os.getenv('TABLE_NAME')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(favorites_table)

@tracer.capture_method 
def list_favorites(event, context):
    logger.info(event)

    user_id = event['requestContext']['authorizer']['claims']['sub']
    logger.info(f"Retrieving favorites for user %s", user_id)

    response = table.query(
        KeyConditionExpression=Key('user_id').eq(user_id)
    )
    items = response['Items']
    # remove the user_id property since it should be transparent to the user
    for item in items:
        item.pop("user_id", None)

    logger.info(items)
    logger.info(f"Found {len(items)} favorite(s) for user.")
    return items


@tracer.capture_lambda_handler
def lambda_handler(event, context):
    try:
        favorites = list_favorites(event, context)
        response = {
            "statusCode": 200,
            "headers": {},
            "body": json.dumps({
                "favorites": favorites
            })
        }
        return response
    except Exception as err:
        logger.exception(err)
        raise
