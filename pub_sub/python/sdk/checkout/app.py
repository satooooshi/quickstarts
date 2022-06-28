from re import I
from dapr.clients import DaprClient
import json
import time
import logging
import uuid
from flask_cors import CORS

from flask import Flask, request, jsonify
from cloudevents.http import from_http

import requests
import os

from fastapi import FastAPI

#app = FastAPI()



logging.basicConfig(level=logging.INFO)


#base_url = os.getenv('BASE_URL', 'http://localhost') + ':' + os.getenv('DAPR_HTTP_PORT', '3500')
base_url = 'http://localhost:3500'
DAPR_STATE_STORE = 'statestore'

app = Flask(__name__)
CORS(
    app,
    supports_credentials=True
)

logging.info('baseurl: ' + base_url)

# Register Dapr pub/sub subscriptions
@app.route('/dapr/subscribe', methods=['GET'])
def subscribe():
    subscriptions = [{
        'pubsubname': 'orderpubsub',
        'topic': 'granted-payment',
        'route': 'granted-payment'
    },
    {
        'pubsubname': 'orderpubsub',
        'topic': 'stock-not-enough',
        'route': 'stock-not-enough'
    },
    {
        'pubsubname': 'orderpubsub',
        'topic': 'balance-not-enough',
        'route': 'balance-not-enough'
    }]
    logging.info('Dapr pub/sub is subscribed to: ' + json.dumps(subscriptions))
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
            'placeAt':'',
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
@app.route('/checkout/<string:catalogId>/<int:amount>/<string:customerId>')
def checkout(catalogId, amount, customerId):
    orderId= 'ord_'+customerId
    order = {
        'orderId':orderId, #str(uuid.uuid4()),
        'catalog':{
            'catalogId':catalogId,
            'amount':amount,
            'price':'',
            'total':'',
        },
        'customer':{
            'customerId':customerId,
            'total':'',
        },
        'processedEvent':'order-accepted',
        'placeAt':time.time()*1000,
        'arriveAt':time.time()*1000,
        'completeAt':''
    }

    state = {
      'key': orderId,
      'value': order
    }

    result = requests.post(
        url='%s/v1.0/state/%s' % (base_url, DAPR_STATE_STORE),
        json=state
    )

    with DaprClient() as client:
        # Publish an event/message using Dapr PubSub
        result = client.publish_event(
            pubsub_name='orderpubsub',
            #topic_name='orders',
            topic_name='started-order',
            data=json.dumps(order),
            data_content_type='application/json',
        )

    #logging.info('Published data: ' + json.dumps(order))
    return jsonify(order), 200#'Order started: catalgId: %s, amount: %d, customerId %s' % (catalogId, amount, customerId)



# https://qiita.com/5zm/items/c8384aa7b7aae924135c
# https://python.civic-apps.com/unixtime-now/
# ミリ秒で欲しいときは1000倍
@app.route('/checkout/<string:catalogId>/<int:amount>/<string:customerId>/<int:placeAtMs>')
def checkoutTest(catalogId, amount, customerId, placeAtMs):
    order = {
        'orderId':  'ord_'+customerId, #str(uuid.uuid4()),
        'catalog':{
            'catalogId':catalogId,
            'amount':amount,
            'price':'',
            'total':'',
        },
        'customer':{
            'customerId':customerId,
            'total':'',
        },
        'processedEvent':'order-accepted',
        'placeAt':placeAtMs,
        'arriveAt':time.time()*1000, # ミリ秒で欲しいときは1000倍
        'completeAt':''
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

    #logging.info('Published data: ' + json.dumps(order))
    time.sleep(1)
    return jsonify(order), 200#'Order started: catalgId: %s, amount: %d, placeAtMs: %f' % (catalogId, amount, placeAtMs)


# https://qiita.com/5zm/items/c8384aa7b7aae924135c
@app.route('/order/<string:customerId>')
def get_order(customerId):
    orderId = 'ord_'+customerId
    result = requests.get(
        url='%s/v1.0/state/%s/%s' % (base_url, DAPR_STATE_STORE, orderId)
    )
    order=result.json()
    logging.info('get_order of customerId: %s: %s', customerId, str(result.json()))
    return jsonify(order), 200#'Order started: catalgId: %s, amount: %d, customerId %s' % (catalogId, amount, customerId)



# FastAPI
# https://fastapi.tiangolo.com/tutorial/path-params/
#@app.get("/items/{item_id}")
#async def read_item(item_id: int):
#    return {"item_id": item_id}

# Dapr subscription in /dapr/subscribe sets up this route
@app.route('/granted-payment', methods=['POST'])
def granted_payment_subscriber():
    event = from_http(request.headers, request.get_data())
    #logging.info('Subscriber received : %s' % event.data)

    ##
    orderId = event.data['orderId'] 
    order = event.data
    # https://note.nkmk.me/python-datetime-timedelta-measure-time/#:~:text=time.time()%20%E3%82%92%E5%88%A9%E7%94%A8,%E7%A7%92%E6%95%B0%E3%81%8C%E6%B1%82%E3%82%81%E3%82%89%E3%82%8C%E3%82%8B%E3%80%82
    # datetime
    order['completeAt']=time.time()*1000
    order['processedEvent']='Order-Success'
    state = [{
      'key': orderId,
      'value': order
    }]
    #logging.info('Order completed: %s %s | %s', state['value']['placeAt'], state['value']['completeAt'],  state['value']['completeAt']- state['value']['placeAt'])
    #logging.info('Order completed: TAT %s', state['value']['completeAt']-state['value']['placeAt'])
    logging.info("arriveAt: %s  completeAt: %s", state[0]['value']['arriveAt'], state[0]['value']['completeAt'])
    with open('perftest.log', 'a') as f:
        print(state[0]['value']['completeAt']-state[0]['value']['arriveAt'], file=f)
    
    #logging.info("placeAt: ", state[0]['value']['placeAt'], ",  completeAt: ", state[0]['value']['completeAt'])

    # Save state into a state store
    result = requests.post(
        url='%s/v1.0/state/%s' % (base_url, DAPR_STATE_STORE),
        json=state
    )
    logging.info('Saving granted-payment order: %s', result.status_code)

    # Get state from a state store
    result = requests.get(
        url='%s/v1.0/state/%s/%s' % (base_url, DAPR_STATE_STORE, orderId)
    )
    logging.info('Getting granted-payment Order: %s', str(result.json()))

    # 200 indicates subscriber successfully got data
    return json.dumps({'success': True}), 200, {
        'ContentType': 'application/json'}


@app.route('/stock-not-enough', methods=['POST'])
def stock_not_enough_subscriber():
    event = from_http(request.headers, request.get_data())
    #logging.info('Subscriber received : %s' % event.data)
    #logging.info('Order canceled, stock-not-enough')

    return json.dumps({'success': True}), 200, {
        'ContentType': 'application/json'}


@app.route('/balance-not-enough', methods=['POST'])
def balance_not_enough_subscriber():
    event = from_http(request.headers, request.get_data())
    #logging.info('Subscriber received : %s' % event.data)
    #logging.info('Order canceled, balance-not-enough')

    return json.dumps({'success': True}), 200, {
        'ContentType': 'application/json'}



app.run(host='0.0.0.0', port=5003)
#app.run(port=5003)

# dapr run --app-id checkout --components-path ../../../components/ --app-port 5003 -- python3 app.py
# http://localhost:5003/checkout/hello/3
