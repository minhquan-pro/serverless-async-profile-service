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
def update_address(event, context):
    logger.info(f"Full event: {event}")

    detail = event['detail']
    line1 = detail['line1']
    line2 = detail['line2']
    city = detail['city']
    state_province = detail['stateProvince']
    postal = detail['postal']
    user_id = detail['userId']
    address_id = detail['addressId']

    if user_id is None or user_id == '':
        raise Exception("User Id could not be found in the incoming event")
    if address_id is None or address_id == '':
        raise Exception("Address Id could not be found in the incoming event")

    logger.info(f"Updating address {address_id} for user {user_id}: {line1}, {line2}, {city}, {state_province}, {postal} in DynamoDb {address_table}")

    table.update_item(
        Key={
            'user_id': user_id,
            'address_id': address_id
        },
        UpdateExpression='SET line1 = :line1, line2 = :line2, city = :city, stateProvince = :stateProvince, postal = :postal',
        ExpressionAttributeValues={
            ':line1': line1,
            ':line2': line2,
            ':city': city,
            ':stateProvince': state_province,
            ':postal': postal
        }
    )

    logger.info(f"Address with ID {address_id} updated")

@tracer.capture_lambda_handler
def lambda_handler(event, context):
    try:
        return update_address(event, context)
    except Exception as err:
        logger.exception(err)
        raise
