import os
import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.data_classes import event_source, SQSEvent

# Globals
logger = Logger()
tracer = Tracer(service="APP")
favorites_table = os.getenv('TABLE_NAME')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(favorites_table)

@tracer.capture_method
def process_event(event: SQSEvent, context):
    logger.debug("Full event: %s", str(event))
    for record in event.records:
        logger.info("Processing event: %s", record)

        restaurant_id = record.body
        user_id = record.message_attributes['UserId'].string_value
        command_name = record.message_attributes['CommandName'].string_value

        if restaurant_id is None or user_id is None or command_name is None:
            raise Exception("Required command properties are missing")

        if command_name == "AddFavorite":
            add_favorite(user_id, restaurant_id)
        elif command_name == "DeleteFavorite":
            delete_favorite(user_id, restaurant_id)
        else:
            raise Exception(f"Command {command_name} not recognized")


@tracer.capture_method
def add_favorite(user_id, restaurant_id):
    """Adds a new favorite restaurant to the user's list"""
    table.put_item(
        Item={
            'user_id': user_id,
            'restaurant_id': restaurant_id
        }
    )
    logger.info(
        "Favorite restaurant with ID %s saved for user %s",
        restaurant_id, user_id)


@tracer.capture_method
def delete_favorite(user_id, restaurant_id):
    """Removes a favorite restaurant from the user's list"""
    logger.info(
        "Deleting favorite restaurant %s for user %s from DynamoDb %s",
        restaurant_id, user_id, favorites_table)

    table.delete_item(
        Key={
            'user_id': user_id,
            'restaurant_id': restaurant_id
        }
    )
    logger.info("Favorite restaurant with ID %s deleted", restaurant_id)


@tracer.capture_lambda_handler
@event_source(data_class=SQSEvent)
def lambda_handler(event: SQSEvent, context):
    """Entrypoint for Lambda"""
    try:
        return process_event(event, context)
    except Exception as err:
        logger.exception(err)
        raise
