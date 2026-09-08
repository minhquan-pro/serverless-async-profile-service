import os
import boto3
from aws_lambda_powertools import Logger, Tracer

# Globals
logger = Logger()
tracer = Tracer(service="APP")
address_table = os.getenv('TABLE_NAME')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(address_table)

@tracer.capture_method
def delete_address(event, context):
    logger.info(f"Full event: {event}")

    detail = event['detail']
    address_id = detail['addressId']
    user_id = detail['userId']

    if user_id is None or user_id == '':
        raise Exception("User Id could not be found in the incoming event")
    if address_id is None or address_id == '':
        raise Exception("Address Id could not be found in the incoming event")

    logger.info(
        f"Deleting address {address_id} for user {user_id} from DynamoDb {address_table}")

    table.delete_item(
        Key={
            'user_id': user_id,
            'address_id': address_id
        }
    )
    logger.info(f"Address with ID {address_id} deleted")


@tracer.capture_lambda_handler
def lambda_handler(event, context):
    """Handles the lambda method invocation"""
    try:
        return delete_address(event, context)
    except Exception as err:
        logger.exception(err)
        raise
