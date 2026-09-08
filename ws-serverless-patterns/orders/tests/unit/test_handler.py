# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import os
import boto3
import uuid
import pytest
from moto import mock_dynamodb
from contextlib import contextmanager
from unittest.mock import patch
from datetime import datetime
from decimal import Decimal

ORDERS_MOCK_TABLE_NAME = 'Orders'
UUID_MOCK_VALUE = uuid.uuid4()
MOCK_USER_ID = 'b949a946-7d55-4a95-b177-b4d4429ea55e'
MOCK_ORDER_ID_1 = '5d6c4bfa-ada8-4586-950e-33ffdebfb816'
MOCK_ORDER_ID_2 = 'db23b410-7822-4dae-abed-ec57e74acdf4'
order_item_1 = {}
order_item_2 = {}


def mock_order_item(user_id, order_id):
    return {
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
            'status': 'SENT',
            'orderTime': '2001-01-01T00:00:00Z'
        }
    }


@contextmanager
def setup_test_environment():
    with mock_dynamodb():
        set_up_dynamodb()
        put_data_dynamodb()
        yield


def set_up_dynamodb():
    dynamodb = boto3.client(
        'dynamodb'
    )
    dynamodb.create_table(
        TableName=ORDERS_MOCK_TABLE_NAME,
        KeySchema=[
            {'AttributeName': 'userId', 'KeyType': 'HASH'},
            {'AttributeName': 'orderId', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'userId', 'AttributeType': 'S'},
            {'AttributeName': 'orderId', 'AttributeType': 'S'},

        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 1,
            'WriteCapacityUnits': 1
        }
    )


def put_data_dynamodb():
    dynamodb = boto3.resource(
        'dynamodb'
    )

    global order_item_1, order_item_2
    order_item_1 = mock_order_item(MOCK_USER_ID, MOCK_ORDER_ID_1)
    order_item_2 = mock_order_item(MOCK_USER_ID, MOCK_ORDER_ID_2)

    orders_table = dynamodb.Table(ORDERS_MOCK_TABLE_NAME)
    orders_table.put_item(
        TableName=ORDERS_MOCK_TABLE_NAME,
        Item=json.loads(json.dumps(order_item_1), parse_float=Decimal)
    )
    orders_table.put_item(
        TableName=ORDERS_MOCK_TABLE_NAME,
        Item=json.loads(json.dumps(order_item_2), parse_float=Decimal)
    )


@patch.dict(os.environ, {'TABLE_NAME': ORDERS_MOCK_TABLE_NAME, 'AWS_XRAY_CONTEXT_MISSING': 'LOG_ERROR'})
def test_list_orders():
    with setup_test_environment():
        from src.api import list_orders
        with open('./events/event-list-orders.json', 'r') as f:
            list_orders_event = json.load(f)

        response = list_orders.lambda_handler(list_orders_event, '')
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        expected_response = {
            'orders':
                [
                    order_item_1['data'], order_item_2['data']
                ]
        }
        assert data == expected_response
