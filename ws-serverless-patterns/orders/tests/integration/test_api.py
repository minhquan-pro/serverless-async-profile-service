import json
import requests
import logging
import time
import uuid

LOGGER = logging.getLogger(__name__)

user1_new_order = {
    "restaurantId": 1,
    "orderId": str(uuid.uuid4()),
    "orderItems": [
        {
            "name": "spaghetti carbonara",
            "price": 9.99,
            "id": 1,
            "quantity": 1
        },
        {
            "name": "Spaghetti aglio e olio",
            "price": 8.99,
            "id": 2,
            "quantity": 2
        },
        {
            "name": "Gorgeous Cotton Pizza",
            "price": 5,
            "id": 10,
            "quantity": 1
        }
    ],
    "totalAmount": 32.97
}


def test_access_to_the_orders_without_authentication(global_config):
  response = requests.post(global_config["Module3ApiEndpoint"] + 'orders')
  assert response.status_code == 401


def test_add_new_order(global_config):
  response = requests.post(
      global_config["Module3ApiEndpoint"] + 'orders',
      data=json.dumps(user1_new_order),
      headers={
          'Authorization': global_config["user1UserIdToken"], 'Content-Type': 'application/json'}
  )
  LOGGER.info("Add new order response: %s", response.text)
  assert response.status_code == 200
  orderInfo = response.json()
  orderId = orderInfo['orderId']
  LOGGER.info("New orderId: %s", orderId)
  global_config['orderId'] = orderId
  assert orderInfo['status'] == "SENT"


def test_list_orders(global_config):
  response = requests.get(
      global_config["Module3ApiEndpoint"] + 'orders',
      headers={
          'Authorization': global_config["user1UserIdToken"], 'Content-Type': 'application/json'}
  )

  LOGGER.info(response.text)
  orders = json.loads(response.text)
  assert len(orders['orders']) == 1
  assert orders['orders'][0]['orderId'] == global_config['orderId']
  assert orders['orders'][0]['totalAmount'] == 32.97
  assert orders['orders'][0]['restaurantId'] == 1
  assert len(orders['orders'][0]['orderItems']) == 3


def test_get_order(global_config):
  print(f"Getting order {global_config['orderId']}")
  print(global_config["Module3ApiEndpoint"] +
        'orders/' + global_config['orderId'])
  response = requests.get(
      global_config["Module3ApiEndpoint"] +
      'orders/' + global_config['orderId'],
      headers={
          'Authorization': global_config["user1UserIdToken"], 'Content-Type': 'application/json'}
  )

  LOGGER.info(response.text)
  orderInfo = json.loads(response.text)
  assert orderInfo['orderId'] == global_config['orderId']
  assert orderInfo['status'] == "SENT"
  assert orderInfo['totalAmount'] == 32.97
  assert orderInfo['restaurantId'] == 1
  assert len(orderInfo['orderItems']) == 3


def test_edit_order(global_config):
  print(f"Modifying order {global_config['orderId']}")

  modifiedOrder = {
      "restaurantId": 1,
      "orderItems": [
          {
              "name": "spicy chicken sandwich",
              "price": 12.99,
              "id": 17,
              "quantity": 1
          },
          {
              "name": "Gorgeous Cotton Pizza",
              "price": 5,
              "id": 10,
              "quantity": 1
          },
          {
              "name": "8\" pepperoni pizza",
              "price": 15,
              "id": 22,
              "quantity": 1
          },
          {
              "name": "spicy chicken sandwich with cheese",
              "price": 14.99,
              "id": 17,
              "quantity": 1
          },
      ],
      "totalAmount": 47.98
  }

  response = requests.put(
      global_config["Module3ApiEndpoint"] +
      'orders/' + global_config['orderId'],
      data=json.dumps(modifiedOrder),
      headers={
          'Authorization': global_config["user1UserIdToken"], 'Content-Type': 'application/json'}
  )

  LOGGER.info(f'Modify order response: {response.text}')
  assert response.status_code == 200
  updatedOrder = response.json()
  assert updatedOrder['totalAmount'] == 47.98
  assert len(updatedOrder['orderItems']) == 4


def test_cancel_order(global_config):
  print(f"Canceling order {global_config['orderId']}")
  response = requests.delete(
      global_config["Module3ApiEndpoint"] +
      'orders/' + global_config['orderId'],
      headers={
          'Authorization': global_config["user1UserIdToken"], 'Content-Type': 'application/json'}
  )

  LOGGER.info(f'Cancel order response: {response.text}')
  assert response.status_code == 200
  orderInfo = json.loads(response.text)
  assert orderInfo['orderId'] == global_config['orderId']
  assert orderInfo['status'] == 'CANCELED'


def test_create_order_idempotency(global_config):
  multiple_order_submission = {
      "restaurantId": 200,
      "orderId": str(uuid.uuid4()),
      "orderItems": [
          {
              "name": "spaghetti carbonara",
              "price": 9.99,
              "id": 123,
              "quantity": 1
          }
      ],
      "totalAmount": 9.99
  }

  response1 = requests.post(
      global_config["Module3ApiEndpoint"] + 'orders',
      data=json.dumps(multiple_order_submission),
      headers={
          'Authorization': global_config["user1UserIdToken"], 'Content-Type': 'application/json'}
  )
  response2 = requests.post(
      global_config["Module3ApiEndpoint"] + 'orders',
      data=json.dumps(multiple_order_submission),
      headers={
          'Authorization': global_config["user1UserIdToken"], 'Content-Type': 'application/json'}
  )
  response3 = requests.post(
      global_config["Module3ApiEndpoint"] + 'orders',
      data=json.dumps(multiple_order_submission),
      headers={
          'Authorization': global_config["user1UserIdToken"], 'Content-Type': 'application/json'}
  )
  LOGGER.info(response1.json())
  orderInfo1 = response1.json()
  orderId1 = orderInfo1['orderId']
  orderInfo2 = response2.json()
  orderId2 = orderInfo2['orderId']
  orderInfo3 = response3.json()
  orderId3 = orderInfo3['orderId']
  assert orderId1 == orderId2
  assert orderId2 == orderId3
  assert orderId1 != global_config['orderId']

  response = requests.get(
      global_config["Module3ApiEndpoint"] + 'orders',
      headers={
          'Authorization': global_config["user1UserIdToken"], 'Content-Type': 'application/json'}
  )

  LOGGER.info(response.text)
  orders = json.loads(response.text)
  # even though we repeated the command 3 times, we should only have 2 orders:
  #   1. One originally created in this test class by test_add_new_order
  #   2. One created in the test method
  assert len(orders['orders']) == 2


def test_cancel_order_in_wrong_status(global_config, acknowledge_order_hook):
  
  response = requests.delete(
      global_config["Module3ApiEndpoint"] +
      'orders/' + global_config['ackOrderId'],
      headers={
          'Authorization': global_config["user1UserIdToken"], 'Content-Type': 'application/json'}
  )

  LOGGER.info(f'Cancel order response: {response.text}')
  
  # Check if the OrderStatusError Exception has been raised, meaning that the status was not 'SENT'
  assert response.status_code == 400


# def test_modify_order_in_wrong_status:
# def test_order_security:
