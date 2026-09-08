from aws_lambda_powertools import Logger, Tracer
from boto3.dynamodb.conditions import Key
import boto3
import os

# Globals
logger = Logger()
tracer = Tracer(service="APP")
ordersTable = os.getenv('TABLE_NAME')
dynamodb = boto3.resource('dynamodb')

@tracer.capture_method 
def get_order(userId, orderId):

    logger.info(f"Retrieving orders for user %s", userId)

    table = dynamodb.Table(ordersTable)
    response = table.query(
        KeyConditionExpression=(Key('userId').eq(userId) & Key('orderId').eq(orderId))
    )
    
    userOrders = []
    for item in response['Items']:
      userOrders.append(item['data'])

    logger.info(userOrders)
    logger.info(f"Found {len(userOrders)} order(s) for user.")

    #TODO: add error handling logic
      
    return userOrders[0]