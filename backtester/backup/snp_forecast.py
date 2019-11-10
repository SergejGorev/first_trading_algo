# -*- coding: utf-8 -*-

from __future__ import print_function

import datetime

import pandas as pd
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis as QDA

from backtester.strategy import Strategy
from backtester.event import SignalEvent
from backtester.backtest import Backtest
from backtester.data import HistoricCSVDataHandler
from backtester.execution import SimulatedExecutionHandler
from backtester.portfolio import Portfolio
from tests.forecasting_ES_movements import create_lagged_series


class SPYDailyForecastStrategy():
    '''
    S&P500 forecast strategy. It uses a QDA to predict the returns for a subsequent time period and then
    generated long/exit signals based on the prediction.
    '''
    def __init__(self, bars, events):
        self.bars = bars
        self.symbol_dict = self.bars.symbol_dict
        self.events = events
        self.datetime_now = datetime.datetime.utcnow()

        self.model_start_date = datetime.datetime(2001,1,10)
        self.model_end_date = datetime.datetime(2005,12,31)
        self.model_start_test_date = datetime.datetime(2005,1,1)

        self.long_market = False
        self.short_market = False
        self.bar_index = 0

        self.model = self.create_symbol_forecast_model()


    def create_symbol_forecast_model(self):
        '''
        It essentially calls forecasting_ES_movements
        :return: model
        '''
        # Create a lagged series of the SP500 US stock market index
        snpret = create_lagged_series(
            list(self.symbol_dict.keys())[0], self.model_start_date,
            self.model_end_date, lags=5
        )

        # Use the prior two days of return as predictor values, with direction as teh response.
        snpret = snpret[snpret['Lag5'].notnull()]
        X = snpret[['Lag1','Lag2']]
        y = snpret['Direction']

        # Create training and test sets
        start_test = self.model_start_test_date
        X_train = X[X.index < start_test]
        X_test = X[X.index >= start_test]
        y_train = y[y.index < start_test]
        y_test = y[y.index >= start_test]

        model = QDA()
        model.fit(X_train, y_train)
        return model

    def calculate_signals(self, event):
        '''
        Calculate the SignalsEvent based on market data.
        '''
        sym = list(self.symbol_dict.keys())[0]
        dt = self.datetime_now

        if event.type == 'MARKET':
            self.bar_index += 1
            if self.bar_index > 5:
                lags = self.bars.get_latest_bars_values(
                    list(self.symbol_dict.keys())[0], 'Adj Close', N=3
                )
                pred_series = pd.Series(
                    {
                        'Lag1': lags[1]*100.0,
                        'Lag2': lags[2]*100.0
                    }
                )
                pred = self.model.predict(pred_series)
                if pred > 0 and not self.long_market:
                    self.long_market = True
                    signal = SignalEvent(1, sym, dt, 'LONG', 1.0)
                    self.events.put(signal)

                if pred < 0 and self.long_market:
                    self.long_market = False
                    signal = SignalEvent(1, sym, dt, 'EXIT', 1.0)
                    self.events.put(signal)


if __name__ == "__main__":
    csv_dir = 'C:\\Users\\Xetra\\PycharmProjects\\first_trading_algo\\data\\'
    symbol_dict = {'SPY': 'ES'}
    initial_capital = 100000.0
    heartbeat = 0.0
    start_date = datetime.datetime(2006,1,3)

    backtest = Backtest(
        csv_dir, symbol_dict, initial_capital, heartbeat, start_date,
        HistoricCSVDataHandler, SimulatedExecutionHandler, Portfolio,
        SPYDailyForecastStrategy
    )
    backtest.simulate_trading()