import simplejson as json
import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext
from datetime import datetime, timedelta
from utils import get_order

# Custom exception
class OrderStatusError(Exception):
    status_code = 400
    
    def __init__(self, message):
        super().__init__(message)

# Globals
logger = Logger()
tracer = Tracer(service="APP")
metrics = Metrics()
ordersTable = os.getenv('TABLE_NAME')
dynamodb = boto3.resource('dynamodb')

@tracer.capture_method
@metrics.log_metrics
def cancel_order(event, context):
    userId = event['requestContext']['authorizer']['claims']['sub']
    orderId = event['pathParameters']['orderId']

    order = get_order(userId, orderId)
    logger.info(f"Current order status for order {orderId} is {order['status']}")
    if order['status'] != 'SENT':
      raise OrderStatusError(f"Order {orderId} with status {order['status']} cannot be canceled. Order must have status SENT to be canceled.")

    orderAge = datetime.utcnow() - datetime.strptime(order['orderTime'], '%Y-%m-%dT%H:%M:%SZ')
    if orderAge.seconds > 600:
      raise OrderStatusError(f"Order {orderId} has been created  {str(round(orderAge.seconds/60, 2))} minutes ago. Order must not be older than 10 minutes to be canceled.")
    
    logger.info('Updating order with new status CANCELED')
    table = dynamodb.Table(ordersTable)
    response = table.update_item(
      Key={'userId': userId, 'orderId': orderId},
      UpdateExpression="set #d.#s=:s",
      ExpressionAttributeNames={
        '#d': 'data',
        '#s': 'status'
      },
      ExpressionAttributeValues={
        ':s': 'CANCELED'
      },
      ReturnValues="ALL_NEW"
    )
    logger.info(json.dumps(response))
    metrics.add_metric(name="OrderCanceled", unit=MetricUnit.Count, value=1)

    return response['Attributes']['data']

@tracer.capture_lambda_handler
def lambda_handler(event, context):
    try:
        updated = cancel_order(event, context)
        response = {
            "statusCode": 200,
            "headers": {},
            "body": json.dumps(updated)
        }
        return response
    except OrderStatusError as oe:
      logger.exception(oe)
      return {
        "statusCode": oe.status_code,
        "body": str(oe)
      }
    except Exception as err:
        logger.exception(err)
        raise
