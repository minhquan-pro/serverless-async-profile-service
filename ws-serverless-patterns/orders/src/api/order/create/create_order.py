import os
import boto3
from decimal import Decimal
import json
import uuid
from datetime import datetime
from aws_lambda_powertools import Logger, Metrics
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.idempotency import (
    IdempotencyConfig, DynamoDBPersistenceLayer, idempotent_function
)

# Globals
logger = Logger()
metrics = Metrics()

orders_table = os.getenv('TABLE_NAME')
idempotency_table = os.getenv('IDEMPOTENCY_TABLE_NAME')
dynamodb = boto3.resource('dynamodb')

persistence_layer = DynamoDBPersistenceLayer(table_name=idempotency_table)
idempotency_config = IdempotencyConfig(event_key_jmespath="powertools_json(body).orderId")

@idempotent_function(data_keyword_argument="event", config=idempotency_config, persistence_store=persistence_layer)
def add_order(event: dict):
    logger.info("Adding a new order")
    detail = json.loads(event['body'])
    logger.info({"operation": "add_order", "order_details": detail})
    restaurant_id = detail['restaurantId']
    total_amount = detail['totalAmount']
    order_items = detail['orderItems']
    user_id = event['requestContext']['authorizer']['claims']['sub']
    order_time = datetime.strftime(datetime.utcnow(), '%Y-%m-%dT%H:%M:%SZ')

    order_id = detail['orderId']

    logger.info(
        f"Saving order {order_id} for user {user_id} at restaurant {restaurant_id}. Total {total_amount} with {len(order_items)} order items")

    ddb_item = {
        'orderId': order_id,
        'userId': user_id,
        'data': {
            'orderId': order_id,
            'userId': user_id,
            'restaurantId': restaurant_id,
            'totalAmount': total_amount,
            'orderItems': order_items,
            'status': 'PLACED',
            'orderTime': order_time,
        }
    }
    ddb_item = json.loads(json.dumps(ddb_item), parse_float=Decimal)

    table = dynamodb.Table(orders_table)
    # We must use conditional expression, otherwise put_item will always replace the original order and will never fail
    table.put_item(Item=ddb_item, ConditionExpression='attribute_not_exists(orderId) AND attribute_not_exists(userId)')

    metrics.add_metric(name="SuccessfulOrder", unit=MetricUnit.Count, value=1)      #SuccessfulOrder
    metrics.add_metric(name="OrderTotal", unit=MetricUnit.Count, value=total_amount) #OrderTotal
    logger.info(f"new Order with ID {order_id} saved")

    detail['orderId'] = order_id
    detail['status'] = 'PLACED'

    return detail


@metrics.log_metrics
@logger.inject_lambda_context
def lambda_handler(event, context: LambdaContext):
    idempotency_config.register_lambda_context(context)
    """Handles the lambda method invocation"""
    try:
        order_detail = add_order(event=event)
        response = {
            "statusCode": 200,
            "headers": {},
            "body": json.dumps(order_detail)
        }
        return response
    except Exception as err:
        logger.exception(err)
        raise
