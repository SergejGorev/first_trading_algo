# -*- coding: utf-8 -*-

from __future__ import print_function

import datetime

import numpy as np

from backtester.strategy import Strategy
from backtester.event import SignalEvent
from backtester.backtest import Backtest
from backtester.data import HistoricCSVDataHandler
from backtester.execution import SimulatedExecutionHandler
from backtester.portfolio import Portfolio

class MovingAvarageCrossStrategy(Strategy):
    '''
    Carries out a basic MACrossover strategy with a short/long simple weighted moving average.
    Default short/long windows are 100/400 period respectively.
    '''
    def __init__(
            self, bars, events, short_window=50, long_window=100
    ):
        '''
        Initialises the Moving Average Cross Strategy
        :param bars: The DataHandler object that provides bar information
        :param events: The event Queue object
        :param short_window: Short Window MA look back
        :param long_window: Long Window MA look back
        '''
        self.bars = bars
        self.symbol_dict = self.bars.symbol_dict
        self.events = events
        self.short_window = short_window
        self.long_window = long_window

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
        '''
        Generates a new set of signals based on the MAC SMA with the short window crossing the long window
        meaning a long entry and vice versa for a shot entry.
        :param event: A MarketEvent object
        '''
        if event.type == 'MARKET':
            for s in self.symbol_dict.keys():
                bars = self.bars.get_latest_bars_values(
                    s, 'Adj Close', N=self.long_window
                )
                bar_date = self.bars.get_latest_bar_datetime(s)
                if bars is not None and bars is not []:
                    short_sma = np.mean(bars[-self.short_window:])
                    long_sma = np.mean(bars[-self.long_window:])

                    symbol = s
                    dt = datetime.datetime.utcnow()
                    sig_dir = ''

                    if short_sma > long_sma and self.bought[s] == 'OUT':
                        print(f'LONG: {bar_date}')
                        sig_dir = 'LONG'
                        signal = SignalEvent(1, symbol, dt, sig_dir, 1.0)
                        self.events.put(signal)
                        self.bought[s] = 'LONG'
                    elif short_sma < long_sma and self.bought[s] == 'LONG':
                        print(f'SHORT: {bar_date}')
                        sig_dir = 'EXIT'
                        signal = SignalEvent(1, symbol, dt, sig_dir, 1.0)
                        self.events.put(signal)
                        self.bought[s] = 'OUT'

if __name__ == "__main__":
    csv_dir = 'data\\'
    # Import and merge dictionaries from TICKER-SYMBOLS.py
    # symbol_dict = {**gd.quandl_cme_futures_map, **gd.quandl_ice_futures_map}
    symbol_dict = {'SPY':'ES'}
    initial_capital = 100000.0
    heartbeat = 0.0
    start_date = datetime.datetime(1990,1,1,0,0,0)
    backtest = Backtest(
        csv_dir, symbol_dict, initial_capital, heartbeat, start_date,
        HistoricCSVDataHandler, SimulatedExecutionHandler, Portfolio,
        MovingAvarageCrossStrategy
    )
    backtest.simulate_trading()