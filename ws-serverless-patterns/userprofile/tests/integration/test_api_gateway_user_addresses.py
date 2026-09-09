import json
import requests
import logging
import time
import uuid
import copy

LOGGER = logging.getLogger(__name__)

user1_new_address = {"line1": "4566 Main", "line2": "Suite 200", "city": "Seattle", "stateProvince": "WA", "postal": "12345"}
user2_new_address = {"line1": "7505 Beverly Blvd", "line2": "Apt 7", "city": "Los Angeles", "stateProvince": "CA", "postal": "90036"}

def test_add_user_address_with_invalid_fields(global_config):
    # LOGGER.info("ID token: %s", global_config["user1UserIdToken"])
    # LOGGER.info("Endpoint: %s", global_config["ProfileApiEndpoint"])
    invalid_address = {"city": "Seattle", "stateProvince": "WA", "postal": "12345"}
    response = requests.post(
        global_config["ProfileApiEndpoint"] + '/address',
        data=json.dumps(invalid_address),
        headers={'Authorization': global_config["user1UserIdToken"], 
            'Content-Type': 'application/json'}
    ) 
    assert response.status_code == 400
    
def test_add_user_address(global_config):
    # LOGGER.info("ID token: %s", global_config["user1UserIdToken"])
    # LOGGER.info("Endpoint: %s", global_config["ProfileApiEndpoint"])
    response = requests.post(
        global_config["ProfileApiEndpoint"] + '/address',
        data=json.dumps(user1_new_address),
        headers={'Authorization': global_config["user1UserIdToken"], 
            'Content-Type': 'application/json'}
    ) 
    assert response.status_code == 200  

    # ensure the async request in the queue has time to be processed
    time.sleep(1)

    response = requests.get(
        global_config["ProfileApiEndpoint"] + '/address',
        headers={'Authorization': global_config["user1UserIdToken"], 
            'Content-Type': 'application/json'}
    )
    assert response.status_code == 200

    response_data = json.loads(response.text)
    # LOGGER.info(response.text)
    assert len(response_data['addresses']) == 1
    assert response_data['addresses'][0]['line1'] == user1_new_address['line1']

def test_update_user_address(global_config):
    # LOGGER.info("ID token: %s", global_config["user1UserIdToken"])
    # LOGGER.info("Endpoint: %s", global_config["ProfileApiEndpoint"])
    user1response = requests.get(
        global_config["ProfileApiEndpoint"] + '/address',
        headers={'Authorization': global_config["user1UserIdToken"], 
            'Content-Type': 'application/json'}
    )

    # LOGGER.info(user1response.text)
    user1addresses = json.loads(user1response.text) 
    updated_address_info = {"line1": "4566 Main", "line2": "Suite 200", "city": "Seattle", "stateProvince": "WA", "postal": "12345"} 

    response = requests.put(
        global_config["ProfileApiEndpoint"] + '/address/' + user1addresses['addresses'][0]['address_id'],
        data=json.dumps(updated_address_info),
        headers={'Authorization': global_config["user1UserIdToken"], 
            'Content-Type': 'application/json'}        
    )
    assert response.status_code == 200  

    time.sleep(2)

    user1response = requests.get(
        global_config["ProfileApiEndpoint"] + '/address',
        headers={'Authorization': global_config["user1UserIdToken"], 
            'Content-Type': 'application/json'}
    )

    # LOGGER.info(user1response.text)
    user1addresses = json.loads(user1response.text) 
    for f in ["line1", "line2", "city", "stateProvince", "postal"]:
        assert user1addresses['addresses'][0][f] == updated_address_info[f]

def test_delete_user_address(global_config):

    user1response = requests.get(
        global_config["ProfileApiEndpoint"] + '/address',
        headers={'Authorization': global_config["user1UserIdToken"], 
            'Content-Type': 'application/json'}
    )

    # LOGGER.info(user1response.text)
    user1addresses = json.loads(user1response.text)  

    response = requests.delete(
        global_config["ProfileApiEndpoint"] + '/address/' + user1addresses['addresses'][0]['address_id'],
        headers={'Authorization': global_config["user1UserIdToken"], 
            'Content-Type': 'application/json'}        
    )
    assert response.status_code == 200

    # ensure the async request in the queue has time to be processed
    time.sleep(2)    

    response = requests.get(
        global_config["ProfileApiEndpoint"] + '/address',
        headers={'Authorization': global_config["user1UserIdToken"], 
            'Content-Type': 'application/json'}
    )
    assert response.status_code == 200

    # LOGGER.info(response.text)
    response_data = json.loads(response.text)
    # search for the address_id to make sure it was deleted
    deleted_address = [a['address_id'] for a in response_data['addresses'] if a['address_id'] == user1addresses['addresses'][0]['address_id']]
    assert len(deleted_address) == 0