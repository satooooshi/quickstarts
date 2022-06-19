from gettext import Catalog
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
    return 'Catalog service / Asynchronous pubsub implementation.'

# https://qiita.com/5zm/items/c8384aa7b7aae924135c
@app.route('/catalog/<string:catalogId>/<int:price>/<int:stock>/<string:name>')
def add_catalog(catalogId, price, stock, name):
    catalog = {
            'catalogId':catalogId,
            'price':price,
            'stock':stock,
            'name':name
        }
    state = [{
      'key': catalogId,
      'value': catalog
    }]
    ## state store should be different from subpub redis instance!!
    # Save state into a state store, state has to be array!!
    result = requests.post(
        url='%s/v1.0/state/%s' % (base_url, DAPR_STATE_STORE),
        json=state
    )
    logging.info('Saving Order: %s', state)

    # Get state from a state store
    result = requests.get(
        url='%s/v1.0/state/%s/%s' % (base_url, DAPR_STATE_STORE, catalogId)
    )
    logging.info('Getting Catalog: ' + str(result.json()))

    # Delete state from the state store
    #result = requests.delete(
    #    url='%s/v1.0/state/%s' % (base_url, DAPR_STATE_STORE),
    #    json=state
    #)
    #logging.info('Deleted Catalog: %s', state)
    ##

    return 'Catalog added: catalogId: %s, price: %d, stock: %d, name: %s' % (catalogId, price, stock, name)

# Register Dapr pub/sub subscriptions
@app.route('/dapr/subscribe', methods=['GET'])
def subscribe():
    subscriptions = [{
        'pubsubname': 'orderpubsub',
        'topic': 'started-order',
        'route': 'started-order'
    }]
    print('Dapr pub/sub is subscribed to: ' + json.dumps(subscriptions))
    return jsonify(subscriptions)


# Dapr subscription in /dapr/subscribe sets up this route
@app.route('/started-order', methods=['POST'])
def started_order_subscriber():
    event = from_http(request.headers, request.get_data())
    print('Subscriber received : %s' % event.data , flush=True)

    ##
    orderId = event.data['orderId'] 
    state = [{
      'key': orderId,
      'value': event.data
    }]

    catalogId = event.data['catalog']['catalogId']
    amount  = event.data['catalog']['amount']
    catalog = requests.get(
        url='%s/v1.0/state/%s/%s' % (base_url, DAPR_STATE_STORE, catalogId)
    )
    logging.info('Got Catalog: ' + str(catalog.json()))

    catalogData=catalog.json()
    ##
    ## cancel event here!!!
    ##
    catalogData['stock']=catalogData['stock']-1
    price = catalogData['price']
    newState=[{
      'key': catalogData['catalogId'],
      'value': catalogData
    }]
    result = requests.post(
        url='%s/v1.0/state/%s' % (base_url, DAPR_STATE_STORE),
        json=newState
    )
    logging.info('Saving newCatalog: %s', newState)

    ##
    ##


    ##
    order=event.data
    #order['catalog']['catalogId']=str('cat_')+str(orderId)
    order['catalog']={
            'catalogId': catalogId,
            'amount': amount,
            'price': price,
            'total': amount*price,
        }
    logging.info('Publishing dataaa: ' + json.dumps(order))
    with DaprClient() as client:
        # Publish an event/message using Dapr PubSub
        result = client.publish_event(
            pubsub_name='orderpubsub',
            topic_name='consumed-catalog',
            data=json.dumps(order),
            data_content_type='application/json',
        )
    logging.info('Published data: ' + json.dumps(order))
    ##

    return json.dumps({'success': True}), 200, {
        'ContentType': 'application/json'}


app.run(host='0.0.0.0', port=5001)

# https://docs.dapr.io/getting-started/quickstarts/pubsub-quickstart/


'''
    # state store should be different from subpub redis instance!!
    # Save state into a state store
    result = requests.post(
        url='%s/v1.0/state/%s' % (base_url, DAPR_STATE_STORE),
        json=[state]
    )
    logging.info('Saving Order: %s', state)

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
    #logging.info('Deleted Order: %s', state)
'''