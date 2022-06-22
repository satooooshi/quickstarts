
from re import I
import json
import time
import logging

import requests
import os


logFile = 'perftest.log'
# DEBUG mode will contains request's DEBUG lines, 
# 06/21/2022 03:39:45 PM - DEBUG: http://localhost:5003 "GET /checkout/111/1/1111 HTTP/1.1" 200 56
#logging.basicConfig( filename = logFile,filemode = 'a',level = logging.INFO,format = '%(asctime)s - %(levelname)s: %(message)s',\
#datefmt = '%m/%d/%Y %I:%M:%S %p' )
logging.basicConfig( filename = logFile,filemode = 'a',level = logging.INFO, format='%(message)s')


# seeds test data
'''
result = requests.get(
    url='http://localhost:5001/catalog/111/120/1000/OperaTicket'
)
result = requests.get(
    url='http://localhost:5002/customer/1111/10000/JohnSmith'
)
'''
result = requests.get(
    url='http://customer.ticketshop.com:31401/order-processor/catalog/111/120/1000/OperaTicket'
)
result = requests.get(
    url='http://customer.ticketshop.com:31401/customer/customer/1111/10000/JohnSmith'
)
for i in range(1, 3):
    catalogId=111
    amount=1
    customerId=1111
    placeAt=time.time()
    result = requests.get(
        #url='http://localhost:5003/checkout/%s/%d/%s/%f' % (catalogId, amount, customerId, placeAt)
        #url='http://localhost:5003/checkout/%s/%d/%s' % (catalogId, amount, customerId)
        url='http://customer.ticketshop.com:31401/checkout/checkout/%s/%d/%s/%f' % (catalogId, amount, customerId, placeAt)

    )
    print('Getting Order: ' + str(result.status_code))
    logging.info("Iam in file2")
    time.sleep(1)

# pip3 install requests
# python3 app.py
