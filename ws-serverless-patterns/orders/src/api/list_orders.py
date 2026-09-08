import simplejson as json
import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from aws_lambda_powertools import Logger, Tracer

# Globals
logger = Logger()
tracer = Tracer(service="APP")
ordersTable = os.getenv('TABLE_NAME')
dynamodb = boto3.resource('dynamodb')

@tracer.capture_method 
def list_orders(event, context):

    user_id = event['requestContext']['authorizer']['claims']['sub']
    logger.info(f"Retrieving orders for user %s", user_id)

    table = dynamodb.Table(ordersTable)
    response = table.query(
        KeyConditionExpression=Key('userId').eq(user_id)
    )

    userOrders = []
    for item in response['Items']:
      userOrders.append(item['data'])

    logger.info(userOrders)
    logger.info(f"Found {len(userOrders)} order(s) for user.")
    return userOrders


@tracer.capture_lambda_handler
def lambda_handler(event, context):
    try:
        orders = list_orders(event, context)
        response = {
            "statusCode": 200,
            "headers": {},
            "body": json.dumps({
                "orders": orders
            })
        }
        return response
    except Exception as err:
        logger.exception(err)
        raise
