import pandas as pd
import numpy as np
import datetime
import os
import sys

# The Idea is to generate Signals from different sources and combine them to create stable trading workframe.
data_dir = 'data\\'
sma_period = 18

def path_generator(cot=None, market=None, weekly=None, daily=None):
    if cot is True:
        for file in os.scandir(data_dir):
            if file.name.endswith('cot.csv'):
                yield file.path, file.name
    if market is True:
        if daily is True:
            for file in os.scandir(data_dir):
                if not file.name.endswith('cot.csv') and \
                        not file.name.endswith('weekly.csv'):
                    yield file.path, file.name
        if weekly is True:
                for file in os.scandir(data_dir):
                    if file.name.endswith('weekly.csv'):
                        yield file.path, file.name

def cot_signal():
    columns = ['Market', 'COT Signal']
    df_cot_signal = pd.DataFrame(columns=columns)
    i = 0
    for path, name in path_generator(cot=True):
        cot_idx = pd.read_csv(path, index_col='Date', parse_dates=True)
        if cot_idx['Commercial Index'].iloc[-1] > 75:
            df_cot_signal.append(df_cot_signal.set_value(i, ['Market', 'COT Signal'], [name.split('_')[0],'Long']))
            i+=1
        if cot_idx['Commercial Index'].iloc[-1] < 25:
            df_cot_signal.append(df_cot_signal.set_value(i, ['Market', 'COT Signal'], [name.split('_')[0],'Short']))
            i+=1
    return df_cot_signal

def daily_price_trigger():
    columns = ['Market', 'Price Trigger']
    df_price_trigger = pd.DataFrame(columns=columns)
    i = 0
    for path, name in path_generator(market=True, daily=True):
        df = pd.read_csv(path, index_col='Date', parse_dates=True)
        df['SMA18'] = df['Settle'].rolling(sma_period).mean()
        df = df[df['SMA18'].notnull()]
        df['long_sma_cross'] = (df['Open'] < df['SMA18']) & (df['SMA18'] < df['High'])
        df['short_sma_cross'] = (df['Open'] > df['SMA18']) & (df['SMA18'] > df['Low'])
        last_long_sma_cross = pd.to_datetime(df[df['long_sma_cross'] == True].last_valid_index())
        last_short_sma_cross = pd.to_datetime(df[df['short_sma_cross'] == True].last_valid_index())
        last_3_days_above = (df['Settle'].iloc[-1] and df['Settle'].iloc[-2] and df['Settle'].iloc[-3]) > df['SMA18'].iloc[-1]
        last_3_days_below = (df['Settle'].iloc[-1] and df['Settle'].iloc[-2] and df['Settle'].iloc[-3]) < df['SMA18'].iloc[-1]
        if last_long_sma_cross >= df.index[-6] and last_3_days_above == True:
            df_price_trigger.append(df_price_trigger.set_value(i, ['Market', 'Price Trigger'], [name.split('.')[0],'Long']))
            i+=1
        if last_short_sma_cross >= df.index[-6] and last_3_days_below == True:
            df_price_trigger.append(df_price_trigger.set_value(i, ['Market', 'Price Trigger'], [name.split('.')[0],'Short']))
            i+=1
    return df_price_trigger

def seasonality_signal():
    pass

def weekly_price_tendency():
    pass

