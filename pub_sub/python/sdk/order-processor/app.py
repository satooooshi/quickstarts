from gettext import Catalog
from flask import Flask, request, jsonify
from cloudevents.http import from_http
import json
from flask_cors import CORS

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
CORS(
    app,
    supports_credentials=True
)

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
    logging.info('Saving Catalog status_code: %s', result.status_code)

    # Get state from a state store
    result = requests.get(
        url='%s/v1.0/state/%s/%s' % (base_url, DAPR_STATE_STORE, catalogId)
    )
    logging.info('Getting Catalog result: ' + str(result.json()))

    # Delete state from the state store
    #result = requests.delete(
    #    url='%s/v1.0/state/%s' % (base_url, DAPR_STATE_STORE),
    #    json=state
    #)
    #logging.info('Deleted Catalog: %s', state)
    ##

    return  jsonify(result.json()),200#'Catalog added: catalogId: %s, price: %d, stock: %d, name: %s' % (catalogId, price, stock, name)



# https://qiita.com/5zm/items/c8384aa7b7aae924135c
@app.route('/getAllCatalog', methods=['GET'])
def get_catalog():

    data = {
          "keys": [ "111", "222" ]
      }
    ## state store should be different from subpub redis instance!!
    # Save state into a state store, state has to be array!!
    result = requests.post(
        url='%s/v1.0/state/%s/bulk' % (base_url, DAPR_STATE_STORE),
        json=data
    )
    logging.info('Getting All Catalog: %s', result.json())

    return jsonify(result.json()), 200



# Register Dapr pub/sub subscriptions
@app.route('/dapr/subscribe', methods=['GET'])
def subscribe():
    subscriptions = [{
        'pubsubname': 'orderpubsub',
        'topic': 'started-order',
        'route': 'started-order'
    },
    {
        'pubsubname': 'orderpubsub',
        'topic': 'balance-not-enough',
        'route': 'balance-not-enough'
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

    # find catalog with catalogId
    catalogId = event.data['catalog']['catalogId']
    amount  = int(event.data['catalog']['amount'])
    resp = requests.get(
        url='%s/v1.0/state/%s/%s' % (base_url, DAPR_STATE_STORE, catalogId)
    )


    if(resp.status_code==200):
        logging.info('200, Got Catalog: %s' + str(resp.json()))
    elif(resp.status_code==204): ## no catalog exists
        logging.info('204, Key is not found.')
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

    catalogData=resp.json()
    stock=int(catalogData['stock'])

    ##
    ## cancel event here!!!
    ## catalog stock is not enough
    if(stock-amount<0):
        logging.info('406, Not Acceptable. No enough stock of %s', catalogId)
        order=event.data
        order['processedEvent']='stock-not-enough. No enough stock of '+catalogId
        logging.info('Publishing dataaa: ' + json.dumps(order))

        with DaprClient() as client:
            # Publish an event/message using Dapr PubSub
                result = client.publish_event(
                pubsub_name='orderpubsub',
                topic_name='stock-not-enough',
                data=json.dumps(order),
                data_content_type='application/json',
            )
        logging.info('Published data: ' + json.dumps(order))
        # This represents subscriber successfully subscribed event, so should return 200
        #return json.dumps({'success': False}), 406, {
        #'ContentType': 'application/json'}
        return json.dumps({'success': True}), 200, {
        'ContentType': 'application/json'}


    


    ##
    catalogData['stock']=stock-amount
    price = catalogData['price']
    newState=[{
      'key': catalogData['catalogId'],
      'value': catalogData
    }]
    result = requests.post(
        url='%s/v1.0/state/%s' % (base_url, DAPR_STATE_STORE),
        json=newState
    )
    logging.info('Saving remaining Catalog: %s', newState)

    ##
    ##


    ##
    order=event.data
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

@app.route('/balance-not-enough', methods=['POST'])
def balance_not_enough_subscriber():
    event = from_http(request.headers, request.get_data())
    print('Subscriber received : %s' % event.data , flush=True)
    print('Order canceled, balance-not-enough')

    # rollback catalog stock here!!
    # find catalog with catalogId
    catalogId = event.data['catalog']['catalogId']
    amount  = event.data['catalog']['amount']
    resp = requests.get(
        url='%s/v1.0/state/%s/%s' % (base_url, DAPR_STATE_STORE, catalogId)
    )
    catalogData=resp.json()
    catalogData['stock']=catalogData['stock']+amount
    newState=[{
      'key': catalogData['catalogId'],
      'value': catalogData
    }]
    result = requests.post(
        url='%s/v1.0/state/%s' % (base_url, DAPR_STATE_STORE),
        json=newState
    )
    logging.info('Saving rollbacked Catalog: %s', newState)

    return json.dumps({'success': True}), 200, {
        'ContentType': 'application/json'}




app.run(host='0.0.0.0', port=5001)
#app.run(port=5001)

# https://docs.dapr.io/getting-started/quickstarts/pubsub-quickstart/

