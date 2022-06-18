from re import I
from dapr.clients import DaprClient
import json
import time
import logging

from flask import Flask, request, jsonify
from cloudevents.http import from_http

import requests
import os

from fastapi import FastAPI

#app = FastAPI()



logging.basicConfig(level=logging.INFO)

base_url = os.getenv('BASE_URL', 'http://localhost') + ':' + os.getenv(
                    'DAPR_HTTP_PORT', '3500')
DAPR_STATE_STORE = 'statestore'

app = Flask(__name__)


# Register Dapr pub/sub subscriptions
@app.route('/dapr/subscribe', methods=['GET'])
def subscribe():
    subscriptions = [{
        'pubsubname': 'orderpubsub',
        'topic': 'granted-payment',
        'route': 'granted-payment'
    }]
    print('Dapr pub/sub is subscribed to: ' + json.dumps(subscriptions))
    return jsonify(subscriptions)


'''
for i in range(1, 3):
    #order = {'orderId': i}
    order = {
        'orderId': i,
        'catalog':{
            'catalogId':'',
            'amount':'',
            'price':'',
            'total':'',
        },
        'customer':{
            'customerId':'',
            'total':'',
            'createdAt':'',
        },
        'processedEvent':'',
    }

    with DaprClient() as client:
        # Publish an event/message using Dapr PubSub
        result = client.publish_event(
            pubsub_name='orderpubsub',
            #topic_name='orders',
            topic_name='started-order',
            data=json.dumps(order),
            data_content_type='application/json',
        )

    logging.info('Published data: ' + json.dumps(order))
    time.sleep(1)
'''


@app.route('/')
def index():
    return 'Order service / Asynchronous pubsub implementation.'

# https://qiita.com/5zm/items/c8384aa7b7aae924135c
@app.route('/checkout/<string:catalogId>/<int:amount>')
def checkout(catalogId, amount):
    order = {
        'orderId': 111,
        'catalog':{
            'catalogId':catalogId,
            'amount':amount,
            'price':'',
            'total':'',
        },
        'customer':{
            'customerId':'',
            'total':'',
            'createdAt':'',
        },
        'processedEvent':'',
    }

    with DaprClient() as client:
        # Publish an event/message using Dapr PubSub
        result = client.publish_event(
            pubsub_name='orderpubsub',
            #topic_name='orders',
            topic_name='started-order',
            data=json.dumps(order),
            data_content_type='application/json',
        )

    logging.info('Published data: ' + json.dumps(order))
    time.sleep(1)
    return 'Order started: catalgId: %s, amount: %d' % (catalogId, amount)

# FastAPI
# https://fastapi.tiangolo.com/tutorial/path-params/
#@app.get("/items/{item_id}")
#async def read_item(item_id: int):
#    return {"item_id": item_id}

# Dapr subscription in /dapr/subscribe sets up this route
@app.route('/granted-payment', methods=['POST'])
def granted_payment_subscriber():
    event = from_http(request.headers, request.get_data())
    print('Subscriber received : %s' % event.data , flush=True)

    ##
    orderId = event.data['orderId'] 
    state = {
      'key': orderId,
      'value': event.data
    }

    # Save state into a state store
    result = requests.post(
        url='%s/v1.0/state/%s' % (base_url, DAPR_STATE_STORE),
        json=state
    )
    logging.info('Saving Order: %s', state)

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



    return json.dumps({'success': True}), 200, {
        'ContentType': 'application/json'}


app.run(port=5003)

# dapr run --app-id checkout --components-path ../../../components/ --app-port 5003 -- python3 app.py
# http://localhost:5003/checkout/hello/3