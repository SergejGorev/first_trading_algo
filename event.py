# -*- coding: utf-8 -*-

from __future__ import print_function


class Event(object):
    '''
    Event is base class providing an interface for all subsequent(inherited) events,
    that will trigger further events in the trading infrastructure.
    '''
    pass

class MarketEvent(Event):
    '''
    MarketEvent occurs when the DataHandler object receives a new update of market data, for any symbols.
    It is used to trigger the Strategy object generating new signals.
    '''

    def __init__(self):
        '''
        Initialises MarketEvent.
        '''
        self.type = 'MARKET'

class SignalEvent(Event):
    '''
    The Strategy object utilizes data to create new SignalEvents.
    Those are utilized by the Portfolio object as advice for how to trade.
    '''

    def __init__(self, strategy_id, symbol, datetime, signal_type, strength):
        '''
        Initialises the SignalEvent.
        :param strategy_id: The unique identifier for the strategy that generated the signal.
        :param symbol: The ticker symbol, e.g. 'GOOG'.
        :param datetime: The timestamp at which the signal was generated.
        :param signal_type: 'Long' ot 'Short'.
        :param strength: An adjustment factor 'suggestion' used to scale quantity at the portfolio level. Useful for pairs strategies.
        '''

        self.type = 'SIGNAL'
        self.strategy_id = strategy_id
        self.symbol = symbol
        self.datetime = datetime
        self.signal_type = signal_type
        self.strength = strength

class OrderEvent(Event):
    '''
    Handles the event of sending an Order to an execution system.
    The order contains a symbol (e.g. GOOG), a type (market of limit), quantity and a direction.
    '''

    def __init__(self, symbol, order_type, quantity, direction):
        '''
        Initiates the order type, setting whether it is a Market order ('MKT') or
        Limit order ('LMT'), has quantity (integral) and its direction ('BUY') or ('SELL').
        :param symbol: The instrument to trade.
        :param order_type: 'MKT' or 'LMT' for Market or Limit.
        :param quantity: Non-negative integer for quantity.
        :param direction: 'BUY' or 'SELL' for long or short.
        '''

        self.type = 'ORDER'
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.direction = direction

    def print_order(self):
        '''
        Outputs the values within the Order.
        '''

        print(
            f'Order: Symbol={self.symbol}, Type={self.order_type}, Quantity={self.quantity}, '
            f'Direction={self.direction}'
        )


class FillEvent(Event):
    '''
    When an ExecutionHandler receives an OrderEvent it must transact the order. Once an order
    has been transacted it generates a FillEvent, which describes the cost of purchase or sale
    as well as the transaction costs, such as fees or slippage.
    '''

    def __init__(self, timeindex, symbol, exchange, quantity, direction, fill_cost, commission=None):
        '''
        Initialises the FillEvent object. Sets the symbol, exchange, quantity, direction,
        fill_cost and an optional commission.

        If commission is not provided, the Fill object will calculate it based on the trade size
        and Interactive Brokers fees.
        :param timeindex: The bar-resolution when the order was filled.
        :param symbol: The instrument which was filled.
        :param exchange: The exchange where the order was filled.
        :param quantity: The filled quantity.
        :param direction: The direction of fill ('BUY' or 'SELL')
        :param fill_cost: The holdings value in dollars.
        :param commission: An optional commission sent from IB.
        '''

        self.type = 'FILL'
        self.timeindex = timeindex
        self.symbol = symbol
        self.exchange =exchange
        self.quantity = quantity
        self.direction = direction
        self.fill_cost = fill_cost
        self.commission = commission

        # Calculate commission
        if commission is None:
            self.commission = self.calculate_ib_commission()
        else:
            self.commission = commission

    def calculate_ib_commission(self):
        '''
        Calculates the fees of trading based on Interactive Brokers fee structure for API, in USD.

        This does not include exchange or ECN fees.

        Based on 'US API Directed Orders':
            https://www.interactivebrokers.com/en/index.php?f=commission&p=stocks2
        :return: commission
        '''
        #todo incorporate future commissions
        full_cost = 1.3
        if self.quantity <= 500:
            full_cost = max(1.3, 0.013 * self.quantity)
        else:
            full_cost = max(1.3, 0.008 * self.quantity)
        return full_cost