import os
import boto3
from decimal import Decimal
import json
import uuid
from datetime import datetime
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

from aws_lambda_powertools.utilities.idempotency import (
    IdempotencyConfig, DynamoDBPersistenceLayer, idempotent
)

# Globals
logger = Logger()
tracer = Tracer(service="APP")
metrics = Metrics()

orders_table = os.getenv('TABLE_NAME')
idempotency_table = os.getenv('IDEMPOTENCY_TABLE_NAME')
dynamodb = boto3.resource('dynamodb')

persistence_layer = DynamoDBPersistenceLayer(table_name=idempotency_table)

# for idempotency, we only care about the body of the request and the user who created it
idempotency_config = IdempotencyConfig(
    event_key_jmespath="powertools_json(body).orderId")

# {
#     "restaurantId": 1,
#     "orderItems": [
#         {
#             "name": "spaghetti carbonara",
#             "price": 9.99,
#             "id": 1,
#             "quantity": 1
#         },
#         {
#             "name": "Spaghetti aglio e olio",
#             "price": 8.99,
#             "id": 2,
#             "quantity": 2
#         },
#         {
#             "name": "Gorgeous Cotton Pizza",
#             "price": 5,
#             "id": 10,
#             "quantity": 1
#         }
#     ],
#     "totalAmount": 32.97
# }


@tracer.capture_method
@metrics.log_metrics
def add_order(event: dict, context: LambdaContext):
    logger.info(event)

    # TODO: sanitize user input for safety
    detail = json.loads(event['body'])
    logger.info(f"Body: {detail}")
    restaurantId = detail['restaurantId']
    totalAmount = detail['totalAmount']
    orderItems = detail['orderItems']
    userId = event['requestContext']['authorizer']['claims']['sub']
    orderTime = datetime.strftime(datetime.utcnow(), '%Y-%m-%dT%H:%M:%SZ')

    orderId = detail['orderId']

    logger.info(
        f"Saving order {orderId} for user {userId} at restaurant {restaurantId}. Total {totalAmount} with {len(orderItems)} order items")

    # TODO: Validate order total
    # TODO: Validate line items
    # TODO: Validate restaurant

    ddb_item = {
        'orderId': orderId,
        'userId': userId,
        'data': {
            'orderId': orderId,
            'userId': userId,
            'restaurantId': restaurantId,
            'totalAmount': totalAmount,
            'orderItems': orderItems,
            'status': 'SENT',
            'orderTime': orderTime,
        }
    }
    ddb_item = json.loads(json.dumps(ddb_item), parse_float=Decimal)

    table = dynamodb.Table(orders_table)
    table.put_item(Item=ddb_item)
    metrics.add_metric(name="SuccessfulOrder", unit=MetricUnit.Count, value=1)
    logger.info(f"new Order with ID {orderId} saved")

    detail['orderId'] = orderId
    detail['status'] = 'SENT'

    return detail


@tracer.capture_lambda_handler
@idempotent(config=idempotency_config, persistence_store=persistence_layer)
def lambda_handler(event, context):
    """Handles the lambda method invocation"""
    try:
        orderDetail = add_order(event, context)
        response = {
            "statusCode": 200,
            "headers": {},
            "body": json.dumps(orderDetail)
        }
        return response
    except Exception as err:
        logger.exception(err)
        raise
