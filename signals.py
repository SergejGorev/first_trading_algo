import pandas as pd
import datetime
import os
import sys

# The Idea is to generate Signals from different sources and combine them to create stable trading workframe.
data_dir = 'data\\'
columns = ['Market', 'COT Signal']
df = pd.DataFrame(columns=columns)

def path_generator(cot=None, market=None):
    if cot is True:
        for file in os.scandir(data_dir):
            if file.name.endswith('cot.csv'):
                return file.path, file.name
    if market is True:
        for file in os.scandir(data_dir):
            if not file.name.endswith('cot.csv'):
                return file.path, file.name

def data_generator(path, cot=None, market=None):
    if cot is True:
        # path, name = path_generator(cot=True)
        yield pd.DataFrame(path)['cot_index']
    if market is True:
        # path, name = path_generator(market=True)
        yield pd.DataFrame(path)

def cot_signal():
    path, name = path_generator(cot=True)
    for cot_idx in data_generator(path, cot=True):
        if cot_idx[cot_idx.iloc[2:-1] > 0.75]:
            df['Market'], df['COT Signal'] = name, 'Long'
        if cot_idx[cot_idx.iloc[2:-1] < 0.25]:
            df['Market'], df['COT Signal'] = name, 'Short'

cot_signal()
print(df)

def seasonality_signal():
    pass

def weekly_price_tendency():
    pass

def daily_price_trigger():
    pass

