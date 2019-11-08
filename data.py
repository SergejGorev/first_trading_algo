# -*- coding: utf-8 -*-

from __future__ import print_function

from abc import ABCMeta, abstractmethod
import datetime
import os, os.path

import numpy as np
import pandas as pd

from event import MarketEvent

class DataHandler(object):
    '''
    DataHandler is an abstract base class (ABC) providing an interface for all subsequent(inherited)
    data handlers (both live and historic) that data handlers must adhere to thereby ensuring
    compatibility with other classes that communicate with them.

    The use of @abstractmethod decorator ist to let python know that the method will be
    overridden in subclasses (this is identical to a pure virtual method in C++)

    The goal of a (derived) DataHandler object is to output a generated ser of bars(OHLCVI)
    for each symbol requested.

    This will replicate how a live strategy would function as current market data be sent
    'down the pipe'. Thus a historic and live system will be treated identically by the
    rest of the backtesting suite.
    '''

    __metaclass__ = ABCMeta
    
    @abstractmethod
    def get_latest_bar(self, symbol):
        '''
        :return: Returns the last bar updated.
        '''
        raise NotImplementedError('Should implement get_latest_bar()')
    
    @abstractmethod
    def get_latest_bars(self, symbol, N=1):
        '''
        :return: Returns the last N bars updated.
        '''
        raise NotImplementedError('Should implement get_latest_bars()')
    
    @abstractmethod
    def get_latest_bar_datetime(self, symbol):
        '''
        :return: Returns a Python datetime object for the last bar.
        '''
        raise NotImplementedError('Should implement get_latest_bar_datetime()')
    
    @abstractmethod
    def get_latest_bar_value(self, symbol, val_type):
        '''
        :return: Returns one of the Open, High, Low, Close, Volume or OI from the last bar.
        '''
        raise NotImplementedError('Should implement get_latest_bar_value()')
    
    @abstractmethod
    def get_latest_bar_values(self, symbol, val_type, N=1):
        '''
        :return: Returns the last N bar values from the latest_symbol list, or N-k if less available.
        '''
        raise NotImplementedError('Should implement get_latest_bar_values()')
    
    @abstractmethod
    def update_bars(self):
        '''
        Pushes the latest bars to the bars_que for each symbol in a tuple OHLCVI format:
        (datetime, open, high, low, close, volume, open interest).
        '''
        raise NotImplementedError('Should implement update_bars()')
    

class HistoricCSVDataHandler(DataHandler):
    '''
    HistoricCSVDataHandler is designed to read CSV files for each requested symbol from disk 
    and provide and interface to obtain the 'latest' bar in a manner identical to a live trading interface.
    
    Specifically it is designed to process multiple CSV files, one for each traded symbol, and convert
    these into a dictionary of pandas DataFrames that can be accessed by the bar methods from DataHandler(ABC).
    '''
    
    def __init__(self, events, csv_dir, symbol_dict):
        '''Initiates the historic data handler by requesting the location of the CSV files 
        and a list/dict of symbols.
        
        It will be assumed that all files are of the form 'symbol.csv', where symbol is a string
        in the dict.
        :param events: The Event Queue.
        :param csv_dir: Absolute directory path to the CSV files.
        :param symbol_dict: A dict of symbol strings
        '''
        
        self.events = events
        self.csv_dir = csv_dir
        self.symbol_dict = symbol_dict
        
        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.continue_backtest = True
        
        self._open_convert_csv_files()
        
    
    def _open_convert_csv_files(self):
        '''
        Opens the CSV files from the data directory, converting them into pandas DataFrame
        within a symbol dictionary.
        
        fro this handler it will be assumed that the data is taken from Quandl. Thus its 
        format will be respected.
        '''
        
        comb_idex = None
        #todo integrate a generator to generate paths
        for s in self.symbol_dict.key():
            path = f'{self.csv_dir}{s}.csv'
            self.symbol_data[s] = pd.read_csv(path, index_col='Date', parse_dates=True, usecols=[
                'Open', 'High', 'Low', 'Settle', 'Volume'
            ]).sort()

            # Combine the index to pad forward values
            if comb_idex is None:
                comb_idex = self.symbol_data[s].index
            else:
                comb_idex.union(self.symbol_data[s].index)

            # Set the latest symbol_data to None
            self.latest_symbol_data[s] = []

        # Reindex the DataFrames
        for s in self.symbol_dict:
            self.symbol_data[s] = self.symbol_data[s].\
                reindex(index=comb_idex, method='pad').iterrows()


# Import and merge dictionaries from get_data.py
import get_data as gd
symbol_dict = {**gd.quandl_cme_futures_map, **gd.quandl_ice_futures_map}