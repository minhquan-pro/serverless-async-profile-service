import simplejson as json
import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from aws_lambda_powertools import Logger, Tracer
from utils import get_order

# Globals
logger = Logger()
tracer = Tracer(service="APP")
ordersTable = os.getenv('TABLE_NAME')
dynamodb = boto3.resource('dynamodb')

@tracer.capture_lambda_handler
def lambda_handler(event, context):
    user_id = event['requestContext']['authorizer']['claims']['sub']
    orderId = event['pathParameters']['orderId']

    try:
        orders = get_order(user_id, orderId)
        response = {
            "statusCode": 200,
            "headers": {},
            "body": json.dumps(orders)
        }
        return response
    except Exception as err:
        logger.exception(err)
        raise
