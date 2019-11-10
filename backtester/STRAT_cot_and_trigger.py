# -*- coding: utf-8 -*-

from __future__ import print_function

import datetime

import pandas as pd
import numpy as np

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
    def __init__(self, bars, events, sma_window=18, cot_ubound=75, cot_lbound=25,
                 bars_momentum=3, cross_bar=6):
        self.bars = bars
        self.symbol_dict = self.bars.symbol_dict
        self.events = events
        self.sma_window = sma_window
        self.cot_ubound = cot_ubound
        self.cot_lbound = cot_lbound
        self.bars_momentum = bars_momentum
        self.cross_bar = cross_bar

        self.long_market = False
        self.short_market = False
        self.bar_index = 0

        # Set to True if a symbol is in the market
        self.bought = self._calculate_initial_bought()

    def _calculate_initial_bought(self):
        '''
        Adds keys to the bought dictionary for all symbols and sets them to 'OUT'.
        Since the Strategy begins out of the market.
        '''
        bought = {}
        for s in self.symbol_dict.keys():
            bought[s] = 'OUT'
        return bought

    def calculate_signals(self, event):

        # if event.type == 'MARKET':
        #     for s in self.symbol_dict

        if event.type == 'MARKET':
            for s in self.symbol_dict.keys():
                bars = self.bars.get_latest_bars_values(
                    s, 'Settle', N=self.sma_window
                )
                bars_close = self.bars.get_latest_bars_values(
                    s, 'Settle', N=self.bars_momentum
                )
                # bars_open = self.bars.get_latest_bars_values(
                #     s, 'Open', N=self.bars_momentum
                # )
                cross_bar_open = self.bars.get_latest_bars_values(
                    s, 'Open', N=self.cross_bar
                )
                cross_bar_close = self.bars.get_latest_bars_values(
                    s, 'Settle', N=self.cross_bar
                )
                cross_bar_high = self.bars.get_latest_bars_values(
                    s, 'High', N=self.cross_bar
                )
                cross_bar_low = self.bars.get_latest_bars_values(
                    s, 'Low', N=self.cross_bar
                )
                cross_bar_date = self.bars.get_latest_bars_datetime(
                    s, N=self.cross_bar
                )
                bars_date = self.bars.get_latest_bars_datetime(
                    s, N=self.bars_momentum
                )
                latest_bar_date = self.bars.get_latest_bar_datetime(s)

                cot_idx = self.bars.get_latest_bar_value(
                    s, 'Commercial Index'
                )
                # if cot_idx is not None and cot_idx is not [] and cot_idx.notnull():
                #
                #
                #
                #     if cot_idx > self.cot_ubound:

                if bars is not None and bars is not []:
                    sma_trigger = np.mean(bars[-self.sma_window:])

                    symbol = s
                    dt = datetime.datetime.utcnow()
                    sig_dir = ''

                    # Define LONG Entry
                    if (cross_bar_open < sma_trigger) and (sma_trigger < cross_bar_high) \
                        and (cross_bar_date >= latest_bar_date) \
                        and (bars_close > sma_trigger) \
                        and (cot_idx > self.cot_ubound):
                        print(f'LONG: {latest_bar_date}')
                        sig_dir = 'LONG'
                        signal = SignalEvent('cot', symbol, dt, sig_dir, 1.0)
                        self.events.put(signal)
                        self.bought[s] = 'LONG'
                    # Define Long Exit
                    elif














