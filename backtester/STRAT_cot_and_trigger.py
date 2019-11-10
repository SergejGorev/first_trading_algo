# -*- coding: utf-8 -*-

from __future__ import print_function

import datetime

import pandas as pd

from backtester.strategy import Strategy
from backtester.event import SignalEvent
from backtester.backtest import Backtest
from backtester.data import HistoricCSVDataHandler
from backtester.execution import SimulatedExecutionHandler
from backtester.portfolio import Portfolio

class COTAndPriceTrigger():
    '''
    COT based strategy with a price trigger to enter and exit the market.
    Price trigger generates LONG/EXIT and SHORT/EXIT signals
    '''
    def __init__(self, bars, events):
        self.bars = bars
        self.symbol_dict = self.bars.symbol_dict
        self.events = events
        self.datetime_now = datetime.datetime.utcnow()

        self.model_start_date = datetime.datetime(2001, 1, 10)
        self.model_end_date = datetime.datetime(2005, 12, 31)
        self.model_start_test_date = datetime.datetime(2005, 1, 1)

        self.long_market = False
        self.short_market = False
        self.bar_index = 0

