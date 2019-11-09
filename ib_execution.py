# -*- coding: utf-8 -*-

from __future__ import print_function

import datetime
import time
try:
    import Queue as queue
except ImportError:
    import queue

from ib.ext.Contract import Contract
from ib.ext.Order import Order
from ib.opt import ibConnection, message

from event import FillEvent, OrderEvent
from execution import ExecutionHandler


class IBExecutionHandler(ExecutionHandler):
    '''
    Handles order execution vie the Interactive Brokers API, for use against accounts when trading live directly.
    '''

    def __init__(self, events, order_routing='SMART', currency='USD'):
        '''
        Initialises the IBExecutionHandler instance.
        :param events: takes knowledge of the Event Queue.
        :param order_routing: requires specification, default is 'SMART'
        :param currency: default currency
        '''
        self.events = events
        self.order_routing = order_routing
        self.currency = currency
        self.fill_dict = {}

        self.tws_conn = self.create_tws_connection()
        self.order_id = self.create_initial_order_id()
        self.register_handlers()


    def _error_handler(self, msg):
        '''
        Handles the capturing of error massages.
        '''
        # Currently no error handling
        print(f'Server Error: {msg}')

    def _reply_handler(self, msg):
        '''
        Handles of server replies
        '''
        # Handle open order orderId processing
        if msg.typeName == 'openOrder' and \
            msg.orderId == self.order_id and \
            not self.fill_dict.has_key(msg.orderId):
            self.create_fill_dict_entry(msg)
        # Handles Fills
        if msg.typeName == 'orderStatus' and \
            msg.status == 'Filled' and \
            self.fill_dict[msg.orderId]['filled'] == False:
            self.create_fill(msg)
        print(f'Server Response: {msg.typeName}, {msg}')

    def create_tws_connection(self):
        '''
        Connect to the TWS running on the usual port of 7496, with a clientId of 10.
        The clientId is chose by us and we will need separate IDs for both the execution connection
        and market data connection, if the latter is used elsewhere.
        :return: TWS Connection
        '''
        tws_conn = ibConnection()
        tws_conn.connect()
        return tws_conn

    def create_initial_order_id(self):
        '''
        Creates the initial order ID used for Interactive Brokers to keep track of
        submitted orders.

        More Sophisticated approach would be the query IB for hte latest available ID
        and use that.
        :return: 1
        '''
        return 1

    def register_handlers(self):
        '''
        Register the error and sever reply massage handling functions.
        '''
        # Assign the error handling function defined above to the TWS connection
        self.tws_conn.register(self._error_handler, 'Error')

        # Assign all of the server reply massages to the reply_handler function defined above
        self.tws_conn.registerAll(self._reply_handler)

    def create_contract(self, symbol, sec_type, exch, prim_exch, curr):
        '''
        Create a Contract object defining what will be purchased, at which exchange
        and in which currency. For more Information see here:
        https://interactivebrokers.github.io/tws-api/classIBApi_1_1Contract.

        todo for futures need also contract month
        :param symbol: The Ticker symbol for the contract.
        :param sec_type: The security type for the contract ('STK' is 'stock')
        :param exch: The exchange to carry out the contract on
        :param prim_exch: the primary exchange to carry out the contract on
        :param curr: The currency in which to purchase the contract
        :return: contract to transact the trade
        '''
        contract = Contract()
        contract.m_symbol = symbol
        contract.m_secType = sec_type
        contract.m_exchange = exch
        contract.m_primaryExch = prim_exch
        contract.m_currency = curr
        return contract

    def create_order(self, order_type, quantity, action):
        '''
        Create an Order object (Market/Limit) to go Long/Short
        :param order_type: 'MKT', 'LMT' for Market or Limit orders
        :param quantity: integer, number of assets to order
        :param action: 'BUY' or 'SELL'
        '''
        order = Order()
        order.m_orderType = order_type
        order.m_totalQuantity = quantity
        order.m_action = action
        return order

    def create_fill_dict_entry(self, msg):
        '''
        Creates an entry in the Fill Dictionary that lists orderIds and provides security information.
        This is needed for the event-driven behaviour of the IB server massage behaviour.
        '''
        self.fill_dict[msg.orderId] = {
            'symbol': msg.contract.m_symbol,
            'exchange': msg.contract.m_exchange,
            'direction': msg.order.m_action,
            'filled': False
        }

    def create_fill(self, msg):
        '''
        Handles the creation of the FillEvent that will be placed into the events queue to an oder being filled.
        '''
        fd = self.fill_dict[msg.orderId]

        # Prepare the fill data
        symbol = fd['symbol']
        exchange  = fd['exchange']
        filled = msg.filled
        direction = fd['direction']
        fill_cost = msg.avgFillPrice

        # Create a fill event object
        fill_event = FillEvent(
            datetime.datetime.utcnow(), symbol, exchange, filled, direction, fill_cost
        )

        # Make sure that multiple multiple messages dont create additional fills.
        self.fill_dict[msg.orderId]['filled'] = True

        # Place the fill event onto the event queue
        self.events.put(fill_event)

    def execute_order(self, event):
        '''
        Creates the necessary InteractiveBrokers order object and submits it to IB vie their API.

        The results are the queried in order to generate a corresponding Fill object, which is
        placed back on the event queue.
        :param event: Contains an Event object with order information.
        '''
        if event.type == 'ORDER':
            # Prepare the parameters for the asset order
            asset = event.symbol
            asset_type = 'STK'
            order_type = event.order_type
            quantity = event.quantity
            direction = event.direction

            # Create the Interactive Brokers contract vie the passed Order Event
            ib_contract = self.create_contract(
                asset, asset_type, self.order_routing, self.order_routing, self.currency
            )

            # Create the Interactive Brokers order vie the passed order event
            ib_order = self.create_order(
                order_type, quantity, direction
            )

            # Use the connection to the send the order to IB
            self.tws_conn.placeOrder(
                self.order_id, ib_contract, ib_order
            )

            # NOTE: Thsi following the line is crucial. It ensures the order goes through.
            time.sleep(1)

            # Increment the order ID for this session
            self.order_id += 1
