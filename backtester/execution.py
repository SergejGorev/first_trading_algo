# -*- coding: utf-8 -*-

from __future__ import print_function

from abc import ABCMeta, abstractmethod
import datetime
try:
    import Queue as queue
except ImportError:
    import queue

from backtester.event import FillEvent
from backtester.data import HistoricCSVDataHandler


class ExecutionHandler(object):
    '''
    The ExecutionHandler abstract class handles the interaction between a set of orders generated by a Portfolio
    and the ultimate set of Fill objects that actually occur in the market.

    The handlers can be used to subclass simulated brokerages or live brokerages, with identical interfaces.
    This allows strategies to be backtested in a very similar manner to the live trading engine.
    '''

    __metaclass__ = ABCMeta

    @abstractmethod
    def execute_order(self, event):
        '''
        Takes an Order event an executes it, producing a Fill event that gets places onto the Events queue.
        :param event: Contains an Event object with order information.
        '''
        raise NotImplementedError('Should implement execute_order()')

#todo in the future, as it comes with live trading, need to generate more sophisticated execution handler
class SimulatedExecutionHandler(ExecutionHandler):
    '''
    The simulated execution handler simply converts all order objects into their equivalent fill objects
    automatically without latency, slippage or fill-ratio issues.

    This allows a straightforward 'first go' test of any strategy, before implementation with more
    sophisticated execution handler.
    '''

    def __init__(self, events, bars):
        '''
        Initialises the handler, setting the event queues up internally.
        :param events: The Queue of Event objects.
        '''
        self.events = events
        self.bars = bars

    def execute_order(self, event):
        '''
        Simply converts Order objects into Fill objects once the order Price is triggered,
        i.e. without any latency, slippage
        or fill ratio problems.
        :param event: Contains an Event object with order information.
        '''
        if event.type == 'ORDER':
            bar_high = self.bars.get_latest_bar_value(
                event.symbol, 'High'
            )
            bar_low = self.bars.get_latest_bar_value(
                event.symbol, 'Low'
            )
            if event.direction == 'BUY' and bar_high >= event.price:
                fill_event = FillEvent(
                    datetime.datetime.utcnow(), event.symbol, 'CME', event.quantity, event.direction,
                    event.price, None
                )
                self.events.put(fill_event)
            if event.direction == 'SELL' and bar_low <= event.price:
                fill_event = FillEvent(
                    datetime.datetime.utcnow(), event.symbol, 'CME', event.quantity, event.direction,
                    event.price, None
                )
                self.events.put(fill_event)