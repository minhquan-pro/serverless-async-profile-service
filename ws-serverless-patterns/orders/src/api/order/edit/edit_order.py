import simplejson as json
import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from aws_lambda_powertools import Logger, Tracer
from decimal import Decimal
from utils import get_order

# Globals
logger = Logger()
tracer = Tracer(service="APP")
ordersTable = os.getenv('TABLE_NAME')
dynamodb = boto3.resource('dynamodb')

def edit_order(event, context):
    userId = event['requestContext']['authorizer']['claims']['sub']
    orderId = event['pathParameters']['orderId']
    newData = json.loads(event['body'], parse_float=Decimal)
    # ensure the userId and orderId exist in the body
    newData['userId'] = userId
    newData['orderId'] = orderId

    order = get_order(userId, orderId)
    logger.info(f"Current order status for order {orderId} is {order['status']}")
    if order['status'] != 'SENT':
      raise Exception(f"Order {orderId} with status {order['status']} cannot be canceled. Order must have status SENT to be canceled.")

    newData['status'] = order['status']
    newData['orderTime'] = order['orderTime']
    ddb_item = {
                'orderId': orderId,
                'userId': userId,
                'data': newData
            }
    ddb_item = json.loads(json.dumps(ddb_item), parse_float=Decimal)

    table = dynamodb.Table(ordersTable)
    response = table.put_item(Item=ddb_item)

    logger.info(f"Put item response:")
    logger.info(response)

    return get_order(userId, orderId)

@tracer.capture_lambda_handler
def lambda_handler(event, context):
    try:
        updated = edit_order(event, context)
        response = {
            "statusCode": 200,
            "headers": {},
            "body": json.dumps(updated)
        }
        return response
    except Exception as err:
        logger.exception(err)
        raise
