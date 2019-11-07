import pandas as pd
import datetime
import os
import sys

# The Idea is to generate Signals from different sources and combine them to create stable trading workframe.
data_dir = 'data\\'
columns = ['Market', 'COT Signal']
plan = pd.DataFrame(columns=columns)

def path_generator(cot=None, market=None):
    if cot is True:
        for file in os.scandir(data_dir):
            if file.name.endswith('cot.csv'):
                yield file.path, file.name
    if market is True:
        for file in os.scandir(data_dir):
            if not file.name.endswith('cot.csv'):
                return file.path, file.name

# def data_generator(path, cot=None, market=None):
#     # if cot is True:
#         # path, name = path_generator(cot=True)
#     yield pd.read_csv(path, index_col='Date', parse_dates=True)#['Commercial Index']
#     # if market is True:
#     #     # path, name = path_generator(market=True)
#     #     yield pd.read_csv(path)
#     # else:
#     #     pass

def cot_signal():
    # path = path_generator(cot=True)
    for path, name in path_generator(cot=True):
        cot_idx = pd.read_csv(path, index_col='Date', parse_dates=True)
        # cot_idx['Commercial Index'] = cot_idx['Commercial Index'].astype(float)
        if cot_idx['Commercial Index'].iloc[-1] > 75:
            plan['Market'], plan['COT Signal'] = name, 'Long'
        if cot_idx['Commercial Index'].iloc[-1] < 25:
            plan['Market'], plan['COT Signal'] = name, 'Short'

cot_signal()
print(plan)

def seasonality_signal():
    pass

def weekly_price_tendency():
    pass

def daily_price_trigger():
    pass

