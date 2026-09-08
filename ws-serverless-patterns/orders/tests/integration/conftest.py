# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import logging
import os
import pytest
import uuid
import json
from datetime import datetime
from decimal import Decimal

APPLICATION_STACK_NAME = os.getenv('USERS_STACK_NAME', None)
MODULE3_STACK_NAME = os.getenv('ORDERS_STACK_NAME', None)
globalConfig = {}
LOGGER = logging.getLogger(__name__)


def get_stack_outputs(stack_name):
    result = {}
    cf_client = boto3.client('cloudformation')
    cf_response = cf_client.describe_stacks(StackName=stack_name)
    outputs = cf_response["Stacks"][0]["Outputs"]
    for output in outputs:
        result[output["OutputKey"]] = output["OutputValue"]
    return result


def create_cognito_accounts():
    result = {}
    sm_client = boto3.client('secretsmanager')
    idp_client = boto3.client('cognito-idp')
    # create regular user account
    sm_response = sm_client.get_random_password(ExcludeCharacters='"''`[]{}():;,$/\\<>|=&',
                                                RequireEachIncludedType=True)
    result["user1UserName"] = "user1User@example.com"
    result["user1UserPassword"] = sm_response["RandomPassword"]
    try:
        idp_client.admin_delete_user(UserPoolId=globalConfig["UserPool"],
                                     Username=result["user1UserName"])
    except idp_client.exceptions.UserNotFoundException:
        print('user1 user haven''t been created previously')
    idp_response = idp_client.admin_create_user(
        UserPoolId=globalConfig["UserPool"],
        Username=result["user1UserName"],
        UserAttributes=[{"Name": "name", "Value": result["user1UserName"]}],
        TemporaryPassword=result["user1UserPassword"],
        MessageAction='SUPPRESS',
        DesiredDeliveryMediums=[],
    )
    # Change the temporary password
    secrets_manager_response = sm_client.get_random_password(
        ExcludeCharacters='"''`[]{}():;,$/\\<>|=&', RequireEachIncludedType=True)
    result["user1UserPassword"] = secrets_manager_response["RandomPassword"]    
    idp_client.admin_set_user_password(
        UserPoolId=globalConfig["UserPool"],
        Username=result["user1UserName"],
        Password=result["user1UserPassword"],
        Permanent=True
    )
    result["user1UserSub"] = idp_response["User"]["Username"]

    # get new user authentication info
    idp_response = idp_client.initiate_auth(
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={
            'USERNAME': result["user1UserName"],
            'PASSWORD': result["user1UserPassword"]
        },
        ClientId=globalConfig["UserPoolClient"],
    )
    result["user1UserIdToken"] = idp_response["AuthenticationResult"]["IdToken"]
    result["user1UserAccessToken"] = idp_response["AuthenticationResult"]["AccessToken"]
    result["user1UserRefreshToken"] = idp_response["AuthenticationResult"]["RefreshToken"]
    # create user2 user account
    sm_response = sm_client.get_random_password(ExcludeCharacters='"''`[]{}():;,$/\\<>|=&',
                                                RequireEachIncludedType=True)
    result["user2UserName"] = "user2User@example.com"
    result["user2UserPassword"] = sm_response["RandomPassword"]
    try:
        idp_client.admin_delete_user(UserPoolId=globalConfig["UserPool"],
                                     Username=result["user2UserName"])
    except idp_client.exceptions.UserNotFoundException:
        print('User2 user haven''t been created previously')
    idp_response = idp_client.admin_create_user(
        UserPoolId=globalConfig["UserPool"],
        Username=result["user2UserName"],
        UserAttributes=[{"Name": "name", "Value": result["user2UserName"]}],
        TemporaryPassword=result["user2UserPassword"],
        MessageAction='SUPPRESS',
        DesiredDeliveryMediums=[],
    )
    # Change the temporary password
    secrets_manager_response = sm_client.get_random_password(
        ExcludeCharacters='"''`[]{}():;,$/\\<>|=&', RequireEachIncludedType=True)
    result["user2UserPassword"] = secrets_manager_response["RandomPassword"]    
    idp_client.admin_set_user_password(
        UserPoolId=globalConfig["UserPool"],
        Username=result["user2UserName"],
        Password=result["user2UserPassword"],
        Permanent=True
    )
    result["user2UserSub"] = idp_response["User"]["Username"]

    # get new user2 user authentication info
    idp_response = idp_client.initiate_auth(
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={
            'USERNAME': result["user2UserName"],
            'PASSWORD': result["user2UserPassword"]
        },
        ClientId=globalConfig["UserPoolClient"],
    )
    result["user2UserIdToken"] = idp_response["AuthenticationResult"]["IdToken"]
    result["user2UserAccessToken"] = idp_response["AuthenticationResult"]["AccessToken"]
    result["user2UserRefreshToken"] = idp_response["AuthenticationResult"]["RefreshToken"]
    return result


def clear_dynamo_tables():
    LOGGER.info("Clearing DynamoDb tables")
    # clear all data from the tables that will be used for testing
    dbd_client = boto3.client('dynamodb')
    db_response = dbd_client.scan(
        TableName=globalConfig['OrdersTable'],
        AttributesToGet=['userId', 'orderId']
    )
    for item in db_response["Items"]:
        dbd_client.delete_item(
            TableName=globalConfig['OrdersTable'],
            Key={'userId': {'S': item['userId']["S"]},
                 'orderId': {'S': item['orderId']["S"]}}
        )

    db_response = dbd_client.scan(
        TableName=globalConfig['IdempotencyTable'],
        AttributesToGet=['id']
    )
    for item in db_response["Items"]:
        dbd_client.delete_item(
            TableName=globalConfig['IdempotencyTable'],
            Key={'id': {'S': item['id']["S"]}}
        )
    return


@pytest.fixture(scope='session')
def global_config(request):
    global globalConfig
    # load outputs of the stacks to test
    globalConfig.update(get_stack_outputs(APPLICATION_STACK_NAME))
    globalConfig.update(get_stack_outputs(MODULE3_STACK_NAME))
    globalConfig.update(create_cognito_accounts())
    clear_dynamo_tables()
    return globalConfig


# This is an additional fixture only for the cancel_order function
# It is needed since at this stage we don't have any means of modifying an order status
# Specifically, this fixture:
# - Before the test: Creates a new order on DynamoDB with an "ACKNOWLEDGED" order status
# - After the test: Cleans up the previously created order
@pytest.fixture(scope='function')
def acknowledge_order_hook(request):

    # Create a DynamoDB client
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(globalConfig['OrdersTable'])

    # First we create a sample order, with a injected "ACKNOWLEDGED" status
    order_id = str(uuid.uuid4())
    user_id = globalConfig['user1UserSub']
    ddb_item = {
        'orderId': order_id,
        'userId': user_id,
        'data': {
            'orderId': order_id,
            'userId': user_id,
            'restaurantId': 2,
            'totalAmount': 32.97,
            'orderItems': [
                {
                    'name': 'spaghetti carbonara',
                    'price': 9.99,
                    'id': 1,
                    'quantity': 1
                },
                {
                    'name': 'Spaghetti aglio e olio',
                    'price': 8.99,
                    'id': 2,
                    'quantity': 2
                },
                {
                    'name': 'Gorgeous Cotton Pizza',
                    'price': 5,
                    'id': 10,
                    'quantity': 1
                }
            ],
            'status': 'ACKNOWLEDGED',
            'orderTime': datetime.strftime(datetime.utcnow(), '%Y-%m-%dT%H:%M:%SZ'),
        }
    }

    ddb_item = json.loads(json.dumps(ddb_item), parse_float=Decimal)

    table.put_item(Item=ddb_item)

    globalConfig['ackOrderId'] = order_id
    # Here we run the test
    yield

    key = {
        'userId': user_id,
        'orderId': order_id
    }

    # After the test has been run, we delete the item
    table.delete_item(Key=key)
