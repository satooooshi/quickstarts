from flask import Flask, request, jsonify
from cloudevents.http import from_http
import json

import time
import logging
import requests
import os

from dapr.clients import DaprClient


logging.basicConfig(level=logging.INFO)

#base_url = os.getenv('BASE_URL', 'http://localhost') + ':' + os.getenv('DAPR_HTTP_PORT', '3500')
base_url = 'http://localhost:3500'
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
    state = [{
      'key': customerId,
      'value': customer
    }]
    ## state store should be different from subpub redis instance!!
    # Save state into a state store, state has to be array!!
    result = requests.post(
        url='%s/v1.0/state/%s' % (base_url, DAPR_STATE_STORE),
        json=state
    )
    logging.info('Saving Catalog: %s', state)
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

    customerId = event.data['customer']['customerId']
    total  = int(event.data['catalog']['total'])
    resp = requests.get(
        url='%s/v1.0/state/%s/%s' % (base_url, DAPR_STATE_STORE, customerId)
    )


    if(resp.status_code==200):
        logging.info('200, Got Customer:'+ str(resp.json()))
    elif(resp.status_code==204): ## no catalog exists
        logging.info('204, Key %s is not found.', customerId )
        return json.dumps({'success': False}), resp.status_code, {
        'ContentType': 'application/json'}
    elif(resp.status_code==400):
        logging.info('400, State store is missing or misconfigured.')
        return json.dumps({'success': False}), resp.status_code, {
        'ContentType': 'application/json'}
    elif(resp.status_code==500):
        logging.info('500, Get state failed.')
        return json.dumps({'success': False}), resp.status_code, {
        'ContentType': 'application/json'}

    customerData=resp.json()
    balance=int(customerData['balance'])

    ##
    ## cancel event here!!!
    if(balance-total<0):
        logging.info('406, Not Acceptable. No enough balance of customer %s', customerId)
        order=event.data
        order['processedEvent']='balance-not-enough. No enough balance of '+customerId
        logging.info('Publishing dataaa: ' + json.dumps(order))

        with DaprClient() as client:
            # Publish an event/message using Dapr PubSub
                result = client.publish_event(
                pubsub_name='orderpubsub',
                topic_name='balance-not-enough',
                data=json.dumps(order),
                data_content_type='application/json',
            )
        logging.info('Published data: ' + json.dumps(order))
        return json.dumps({'success': True}), 200, {
        'ContentType': 'application/json'}


    ##
    customerData['balance']=balance-total
    newState=[{
      'key': customerData['customerId'],
      'value': customerData
    }]
    result = requests.post(
        url='%s/v1.0/state/%s' % (base_url, DAPR_STATE_STORE),
        json=newState
    )
    logging.info('Saving Customer with remaining balance: %s', newState)

    ##
    order=event.data
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

    return json.dumps({'success': True}), 200, {
        'ContentType': 'application/json'}

app.run(host='0.0.0.0', port=5002)
#app.run( port=5002)

# https://docs.dapr.io/getting-started/quickstarts/pubsub-quickstart/



