# -*- coding: utf-8 -*-

from __future__ import print_function

try:
    import Queue as queue
except ImportError:
    import queue

import pandas as pd

from backtester.event import OrderEvent
from backtester.performance import create_sharpe_ratio, create_drawdowns
from backtester.TICKER_VALUE import s_tick_amount, s_tick_value

class Portfolio(object):
    '''
    The Portfolio class handles the position and market value of all instruments at a resolution of a bar
    i.e. secondly, minutely, 5-min, 30-min, 60-min or EOD.

    The positions DataFrame stores a time-index of the quantity of positions held.

    The holdings DataFrame stores the cash and total market holdings value of each symbol for particular
    time-index as well as the percentage change in portfolio total across bars.
    '''

    def __init__(self, bars, events, start_date, initial_capital=100000.0):
        '''
        Initialises the portfolio with bars and an event queue. Also includes a starting datetime index
        and initial capital (USD unless otherwise started)
        :param bars: The DataHandler object with current market data.
        :param events: The Event Queue object.
        :param start_date: The start date (bar) of the portfolio.
        :param initial_capital: The starting capital in USD.
        '''
        self.bars = bars
        self.events = events
        self.symbol_dict = self.bars.symbol_dict
        self.start_date = start_date
        self.initial_capital = initial_capital
        self.slippage = 2

        self.all_positions = self.construct_all_positions()
        self.current_positions = dict( (k,v) for k,v in [(s,0) for s in self.symbol_dict.keys()] )

        self.all_holdings = self.construct_all_holdings()
        self.current_holdings = self.construct_current_holdings()

    def construct_all_positions(self):
        '''
        Construct the positions list using the start_date to determine when the time index will begin.
        :return: Dictionary
        '''
        d = dict( (k,v) for k,v in [(s,0) for s in self.symbol_dict.keys()] )
        d['datetime'] = self.start_date
        return [d]

    def construct_all_holdings(self):
        '''
        Construct the holdings list using the start_date to determine when the time index will begin.
        :return: Dictionary
        '''
        d = dict((k, v) for k, v in [(s, 0) for s in self.symbol_dict.keys()])
        d['datetime'] = self.start_date
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return [d]

    def construct_current_holdings(self):
        '''
        This constructs the dictionary which will hold the instantaneous value of the portfolio across all symbol
        :return: Dictionary
        '''
        d = dict( (k,v) for k,v in [(s,0) for s in self.symbol_dict.keys()] )
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return d

    def update_timeindex(self, event):
        '''
        Adds a new record to the positions matrix for the current market data bar. This reflects the PREVIOUS bar,
        i.e. all current market data at this stage is known (OHLCV).
        :param event: Makes use of a MarketEvent from the events queue.
        '''
        latest_datetime = self.bars.get_latest_bar_datetime(
            list(self.symbol_dict.keys())[0]
        )

        # Update positions
        # ================
        dp = dict((k, v) for k, v in [(s, 0) for s in self.symbol_dict.keys()] )
        dp['datetime'] = latest_datetime

        for s in self.symbol_dict.keys():
            dp[s] = self.current_positions[s]

        #Append the current positions
        self.all_positions.append(dp)

        # Update holdings
        # ===============
        dh = dict((k, v) for k, v in [(s, 0) for s in self.symbol_dict.keys()])
        dh['datetime'] = latest_datetime
        dh['cash'] = self.current_holdings['cash']
        dh['commission'] = self.current_holdings['commission']
        dh['total'] = self.current_holdings['cash']

        self.fill_price = {}
        for s in self.symbol_dict.keys():
            # Approximation to the real value for each future symbol
            if event.type == 'FILL':
                self.fill_price[s] = event.price
            try:
                market_value = self.current_positions[s] * \
                               (self.bars.get_latest_bar_value(s, 'Settle') - self.fill_price[s] ) / \
                               s_tick_amount[s] * s_tick_value[s]
                dh[s] = market_value
                dh['total'] += market_value
            except:
                pass

        # Append the current holdings
        self.all_holdings.append(dh)

    def update_positions_from_fill(self, fill):
        '''
        This method determines whether a FillEvent is a Buy or Sell and then updates the current_positions dictionary.
        :param fill: Takes the Fill object and updates the position matrix.
        '''

        # Check whether the fill is a buy or sell
        fill_dir = 0
        if fill.direction == 'BUY':
            fill_dir = 1
        if fill.direction == 'SELL':
            fill_dir = -1

        # Update positions list with new quantities
        self.current_positions[fill.symbol] += fill_dir*fill.quantity

    def update_holdings_from_fill(self, fill):
        '''
        This method determines whether a FillEvent is a Buy or Sell and then updates the current_holdings dictionary.
        Essentially adding up fill cost associated with trading in general. (SLIPPAGE,COMMISSION)
        :param fill: Takes the Fill object and updates the holdings matrix to reflect the holding value.
        '''

        # Check whether the fill is a buy or sell
        # And calculate fill cost with 2 tick slippage
        fill_dir = 0
        if fill.direction == 'BUY':
            fill_dir = 1
        if fill.direction == 'SELL':
            fill_dir = -1


        # Update holdings list with new quantities
        cost = fill_dir * (self.bars.get_latest_bar_value(fill.symbol, 'Settle') - fill.price) / \
               s_tick_amount[fill.symbol] * self.slippage * fill.quantity
        self.current_holdings[fill.symbol] += cost
        self.current_holdings['commission'] += fill.commission
        self.current_holdings['cash'] -= (cost + fill.commission)
        self.current_holdings['total'] -= (cost + fill.commission)

    def update_fill(self, event):
        '''
        Executes two preceding methods, update_holdings_from_fill and update_positions_from_fill
        upon receipt of a fill event.
        :param event: Takes FillEvent
        '''
        if event.type == 'FILL':
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)

    def generate_naive_order(self, signal):
        '''
        Generating OrderEvents upon the receipt of one or more SignalEvents. Files an Order object as a
        constant quantity sizing of the signal object, without risk management or position sizing considerations.
        :param signal: The tuple containing signal information.
        :return: Order
        '''
        order = None

        symbol = signal.symbol
        signal_type = signal.signal_type
        price = signal.price
        strength = signal.strength

        mkt_quantity = 1
        cur_quantity = self.current_positions[symbol]
        order_type = 'MKT'

        if signal_type == 'LONG' and cur_quantity == 0:
            order = OrderEvent(symbol,order_type,price,mkt_quantity,'BUY')
        if signal_type == 'SHORT' and cur_quantity == 0:
            order = OrderEvent(symbol,order_type,price,mkt_quantity,'SELL')

        if signal_type == 'LONG STOP EXIT' and cur_quantity > 0:
            order = OrderEvent(symbol,order_type,price, abs(cur_quantity), 'SELL')
        if signal_type == 'LONG TAKE PROFIT EXIT' and cur_quantity > 0:
            order = OrderEvent(symbol,order_type,price, abs(cur_quantity), 'SELL')

        if signal_type == 'SHORT STOP EXIT' and cur_quantity < 0:
            order = OrderEvent(symbol,order_type,price, abs(cur_quantity), 'BUY')
        if signal_type == 'SHORT TAKE PROFIT EXIT' and cur_quantity < 0:
            order = OrderEvent(symbol,order_type,price, abs(cur_quantity), 'BUY')

        return order

    def update_signal(self, event):
        '''
        This method simply calls the above method and adds the generated order to events queue.
        Acts on SignalEvent to generate new orders based on the portfolio logic.
        '''
        if event.type == 'SIGNAL':
            order_event = self.generate_naive_order(event)
            self.events.put(order_event)

    def create_equity_curve_dataframe(self):
        '''
        :return: a pandas DataFrame from the all_holdings list of dictionaries.
        '''
        curve = pd.DataFrame(self.all_holdings)
        curve.set_index('datetime', inplace=True)
        curve['returns'] = curve['total'].pct_change()
        curve['equity_curve'] = (1.0+curve['returns']).cumprod()
        self.equity_curve = curve

    def output_summary_stats(self):
        '''
        :return: a list of summary statistics for the Portfolio.
        '''
        total_return = self.equity_curve['equity_curve'][-1]
        returns = self.equity_curve['returns']
        pnl = self.equity_curve['equity_curve']

        sharpe_ratio = create_sharpe_ratio(returns, periods=252)
        drawdown, max_dd, dd_duration = create_drawdowns(pnl)
        self.equity_curve['drawdown'] = drawdown

        stats = [
            ('Total Return', f'{round((total_return - 1.0) * 100.0,2)}%'),
            ('Sharpe Ratio', f'{round(sharpe_ratio,2)}'),
            ('Max Drawdown', f'{round(max_dd * 100.0,2)}%'),
            ('Drawdown', f'{dd_duration}')
        ]
        self.equity_curve.to_csv('backtester\\equity.csv')
        return stats
