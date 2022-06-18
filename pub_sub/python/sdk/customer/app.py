from flask import Flask, request, jsonify
from cloudevents.http import from_http
import json

import time
import logging
import requests
import os

from dapr.clients import DaprClient


logging.basicConfig(level=logging.INFO)

base_url = os.getenv('BASE_URL', 'http://localhost') + ':' + os.getenv(
                    'DAPR_HTTP_PORT', '3500')
DAPR_STATE_STORE = 'statestore'

app = Flask(__name__)

@app.route('/')
def index():
    return 'Customer service / Asynchronous pubsub implementation.'

@app.route('/customer/<string:customerId>/<int:balance>/<string:name>')
def add_customer(customerId, balance,  name):
    customer = {
            'customerId':customerId,
            'balance':balance,
            'name':name,
        }
    return 'Customer added: customerId: %s, balance: %d, name: %s' % (customerId, balance, name)

# Register Dapr pub/sub subscriptions
@app.route('/dapr/subscribe', methods=['GET'])
def subscribe():
    subscriptions = [{
        'pubsubname': 'orderpubsub',
        'topic': 'consumed-catalog',
        'route': 'consumed-catalog'
    }]
    print('Dapr pub/sub is subscribed to: ' + json.dumps(subscriptions))
    return jsonify(subscriptions)


# Dapr subscription in /dapr/subscribe sets up this route
@app.route('/consumed-catalog', methods=['POST'])
def consumed_catalog_subscriber():
    event = from_http(request.headers, request.get_data())
    print('Subscriber received : %s' % event.data , flush=True)

    ##
    ## TODO key is appended automatically??
    orderId = event.data['orderId']
    state = {
      'key': orderId,
      'value': event.data
    }

    ##
    # Save state into a state store
    result = requests.post(
        url='%s/v1.0/state/%s' % (base_url, DAPR_STATE_STORE),
        json=state
    )
    logging.info('Saving Orderrrr: %s', state)

    # Get state from a state store
    result = requests.get(
        url='%s/v1.0/state/%s/%s' % (base_url, DAPR_STATE_STORE, orderId)
    )
    #logging.info('Getting Order: ' + str(result.json()))

    # Delete state from the state store
    result = requests.delete(
        url='%s/v1.0/state/%s' % (base_url, DAPR_STATE_STORE),
        json=state
    )
    #logging.info('Deleted Order: %s', state)
    ##


    ##
    order=event.data
    order['customer']['customerId']=str('cus_')+str(state['key'])
    logging.info('Publishing dataaa: ' + json.dumps(order))
    with DaprClient() as client:
        # Publish an event/message using Dapr PubSub
        result = client.publish_event(
            pubsub_name='orderpubsub',
            topic_name='granted-payment',
            data=json.dumps(order),
            data_content_type='application/json',
        )
    logging.info('Published data: ' + json.dumps(order))

    ##
    

    return json.dumps({'success': True}), 200, {
        'ContentType': 'application/json'}

app.run(port=5002)

# https://docs.dapr.io/getting-started/quickstarts/pubsub-quickstart/


'''
    result = requests.post(
        url='%s/v1.0/state/%s' % (base_url, DAPR_STATE_STORE),
        json=state
    )
    logging.info('Saving Orderrrr: %s', state)

    # Get state from a state store
    result = requests.get(
        url='%s/v1.0/state/%s/%s' % (base_url, DAPR_STATE_STORE, orderId)
    )
    logging.info('Getting Order: ' + str(result.json()))

    # Delete state from the state store
    result = requests.delete(
        url='%s/v1.0/state/%s' % (base_url, DAPR_STATE_STORE),
        json=state
    )
    logging.info('Deleted Order: %s', state)
'''

'''
    order=event.data
    order['customer']['customerId']=str('cus_')+str(state['key'])
    logging.info('Publishing dataaa: ' + json.dumps(order))
    with DaprClient() as client:
        # Publish an event/message using Dapr PubSub
        result = client.publish_event(
            pubsub_name='orderpubsub',
            topic_name='granted-payment',
            data=json.dumps(order),
            data_content_type='application/json',
        )
    logging.info('Published data: ' + json.dumps(order))
'''