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
from backtester.TICKER_VALUE import s_tick_amount

class COTAndPriceTriggerSrategy():
    '''
    COT based strategy with a price trigger to enter and exit the market.
    Price trigger generates LONG/EXIT and SHORT/EXIT signals
    '''
    def __init__(self, bars, events, sma_window=18, cot_ubound=75.0, cot_lbound=25.0,
                 bars_momentum=3, cross_bar=5):
        self.bars = bars
        self.symbol_dict = self.bars.symbol_dict
        self.events = events
        self.sma_window = sma_window
        self.cot_ubound = cot_ubound
        self.cot_lbound = cot_lbound
        self.bars_momentum = bars_momentum + 1
        self.cross_bar = cross_bar



        # Set to True if a symbol is in the market
        self.bought = self._calculate_initial_bought()
        self.entry_price = self._calculate_entry_price()
        self.stop = self._calculate_stop_prices()
        self.take_profit = self._calculate_take_profit_prices()
        self.cross_bar_date = self._calculate_cross_bar_date()
        self.window_cond = self._calculate_cross_bar_window_cond()
        self.cross_bar_low = self._calculate_cross_bar_low()
        self.cross_bar_high = self._calculate_cross_bar_high()
        self.cross_bar_long = self._calculate_cross_bar_long_condition()
        self.cross_bar_short = self._calculate_cross_bar_short_condition()

    def _calculate_initial_bought(self):
        '''
        Adds keys to the bought dictionary for all symbols and sets them to 'OUT'.
        Since the Strategy begins out of the market.
        '''
        bought = {}
        for s in self.symbol_dict.keys():
            bought[s] = 'OUT'
        return bought

    def _calculate_entry_price(self):
        entry_price = {}
        for s in self.symbol_dict.keys():
            entry_price[s] = 0
        return entry_price

    def _calculate_stop_prices(self):
        '''
        Adds for each key a stop price if entry signal is generated
        '''
        stop = {}
        for s in self.symbol_dict.keys():
            stop[s] = 0
        return stop

    def _calculate_take_profit_prices(self):
        take_profit = {}
        for s in self.symbol_dict.keys():
            take_profit[s] = 0
        return take_profit

    def _calculate_cross_bar_date(self):
        cross_bar_date = {}
        for s in self.symbol_dict.keys():
            cross_bar_date[s] = 0
        return cross_bar_date

    def _calculate_cross_bar_window_cond(self):
        window_cond = {}
        for s in self.symbol_dict.keys():
            window_cond[s] = False
        return window_cond

    def _calculate_cross_bar_low(self):
        cross_bar_low = {}
        for s in self.symbol_dict.keys():
            cross_bar_low[s] = 0
        return cross_bar_low

    def _calculate_cross_bar_high(self):
        cross_bar_high = {}
        for s in self.symbol_dict.keys():
            cross_bar_high[s] = 0
        return cross_bar_high

    def _calculate_cross_bar_long_condition(self):
        cross_bar_long = {}
        for s in self.symbol_dict.keys():
            cross_bar_long[s] = False
        return cross_bar_long

    def _calculate_cross_bar_short_condition(self):
        cross_bar_short = {}
        for s in self.symbol_dict.keys():
            cross_bar_short[s] = False
        return cross_bar_short

    def calculate_signals(self, event):

        if event.type == 'MARKET':
            for s in self.symbol_dict.keys():
                bars = self.bars.get_latest_bars_values(
                    s, 'Settle', N=self.sma_window
                )
                bars_close = self.bars.get_latest_bars_values(
                    s, 'Settle', N=self.bars_momentum
                )
                bars_high = self.bars.get_latest_bars_values(
                    s, 'High', N=self.bars_momentum
                )
                bars_low = self.bars.get_latest_bars_values(
                    s, 'Low', N=self.bars_momentum
                )
                latest_bar_date = self.bars.get_latest_bar_datetime(s)
                latest_bar_high = self.bars.get_latest_bar_value(
                    s, 'High'
                )
                latest_bar_low = self.bars.get_latest_bar_value(
                    s, 'Low'
                )
                latest_bar_open = self.bars.get_latest_bar_value(
                    s, 'Open'
                )
                cot_idx = self.bars.get_latest_bar_value(
                    s, 'Commercial Index'
                )

                if bars is not None and bars is not [] and pd.notnull(cot_idx):
                    sma_trigger = np.mean(bars[-self.sma_window:])

                    symbol = s
                    dt = datetime.datetime.utcnow()
                    sig_dir = ''


                    # Define Cross bars
                    self.cross_bar_long[s] = (latest_bar_open < sma_trigger) & (sma_trigger < latest_bar_high)
                    self.cross_bar_short[s] = (latest_bar_open > sma_trigger) & (sma_trigger > latest_bar_low)

                    # Define cross_bar high and low and date in order to set stop
                    if self.cross_bar_short[s] or self.cross_bar_long[s]:
                        self.cross_bar_low[s] = latest_bar_low
                        self.cross_bar_high[s] = latest_bar_high
                        self.cross_bar_date[s] = latest_bar_date

                    # Define window condition for how much to look back since crossing bar
                    try:
                        self.window_cond[s] = (self.bars_momentum <= (latest_bar_date - self.cross_bar_date[s]).days <= self.cross_bar)
                    except:
                        pass

                    #### Define LONG Entry Signal ####
                    mom_long_cond = all(np.where(bars_close[:-1] > sma_trigger, True, False))
                    cot_long_cond = cot_idx > self.cot_ubound
                    if self.window_cond[s] \
                            and mom_long_cond \
                            and cot_long_cond \
                            and self.bought[s] == 'OUT':
                        print(f'{s} LONG: {latest_bar_date} at {max(bars_high[:-1])}')
                        self.stop[s] = self.cross_bar_low[s]
                        self.take_profit[s] = max(bars_high[:-1]) + \
                                    (max(bars_high[:-1]) / s_tick_amount[s]  - self.stop[s] / s_tick_amount[s]) * \
                                    s_tick_amount[s]
                        sig_dir = 'LONG'
                        signal = SignalEvent('cot', symbol, dt, sig_dir, max(bars_high[:-1]), 1.0)
                        self.events.put(signal)
                        self.bought[s] = 'LONG'

                    # Define Long Stop Exit Signal
                    if latest_bar_low <= self.stop[s] and self.bought[s] == 'LONG':
                        print(f'{s} LONG STOP EXIT: {latest_bar_date} at {self.stop[s]}')
                        sig_dir = 'LONG STOP EXIT'
                        signal = SignalEvent('cot', symbol, dt, sig_dir, self.stop[s], 1.0)
                        self.events.put(signal)
                        self.bought[s] = 'OUT'

                    # Define Long Take Profit Exit Signal
                    if latest_bar_high >= self.take_profit[s] and self.bought[s] == 'LONG':
                        print(f'{s} LONG TAKE PROFIT EXIT: {latest_bar_date} at {self.take_profit[s]}')
                        sig_dir = 'LONG TAKE PROFIT EXIT'
                        signal = SignalEvent('cot', symbol, dt, sig_dir, self.take_profit[s], 1.0)
                        self.events.put(signal)
                        self.bought[s] = 'OUT'


                    #### Define Short Entry Signal ####
                    mom_short_cond = all(np.where(bars_close[:-1] < sma_trigger, True, False))
                    cot_short_cond = (cot_idx < self.cot_ubound)
                    if self.window_cond[s] \
                            and mom_short_cond \
                            and cot_short_cond \
                            and self.bought[s] == 'OUT':
                        print(f'{s} SHORT: {latest_bar_date} at {min(bars_low[:-1])}')
                        self.stop[s] = self.cross_bar_high[s]
                        self.take_profit[s] = min(bars_low[:-1]) + \
                                (min(bars_low[:-1]) / s_tick_amount[s]  - self.stop[s] / s_tick_amount[s]) * \
                                s_tick_amount[s]
                        sig_dir = 'SHORT'
                        signal = SignalEvent('cot', symbol, dt, sig_dir, min(bars_low[:-1]), 1.0)
                        self.events.put(signal)
                        self.bought[s] = 'SHORT'

                    # Define Short Stop Exit Signal
                    if latest_bar_high >= self.stop[s] and self.bought[s] == 'SHORT':
                        print(f'{s} SHORT STOP EXIT: {latest_bar_date} at {self.stop[s]}')
                        sig_dir = 'SHORT STOP EXIT'
                        signal = SignalEvent('cot', symbol, dt, sig_dir, self.stop[s], 1.0)
                        self.events.put(signal)
                        self.bought[s] = 'OUT'

                    # Define Short Take Profit Exit Signal
                    if latest_bar_low <= self.take_profit[s] and self.bought[s] == 'SHORT':
                        print(f'{s} SHORT TAKE PROFIT EXIT: {latest_bar_date} at {self.take_profit[s]}')
                        sig_dir = 'SHORT TAKE PROFIT EXIT'
                        signal = SignalEvent('cot', symbol, dt, sig_dir, self.take_profit[s], 1.0)
                        self.events.put(signal)
                        self.bought[s] = 'OUT'


if __name__ == "__main__":
    csv_dir = 'data\\'
    # import and merge dictionaries from TICKER_SYMBOLS.py
    import backtester.TICKER_SYMBOLS as symbols
    # symbol_dict = {**symbols.quandl_cme_futures_map, **symbols.quandl_ice_futures_map}
    symbol_dict = {'ES':'ES'}
    initial_capital = 100000.0
    heartbeat = 0.0
    start_date = datetime.datetime(1990,1,1,0,0,0)
    backtest = Backtest(
        csv_dir, symbol_dict, initial_capital, heartbeat, start_date,
        HistoricCSVDataHandler, SimulatedExecutionHandler, Portfolio,
        COTAndPriceTriggerSrategy
    )
    backtest.simulate_trading()












