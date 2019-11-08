import pandas as pd
import numpy as np
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.seasonal import STL
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import matplotlib.pyplot as plt

import seaborn as sns
import warnings
warnings.filterwarnings('ignore')


def plot_seasonal_decompose(data, model, freq=252):
    '''
    Summary:
    Plots trend, seasonality and residual
    :param data: DataFrame, Series
    :param model: multiplicative or additive
    :return: decomposition(obj): value of statsmodels.tsa.seasonal.seasonal_decompose
    '''
    decomposition = seasonal_decompose(data,model=model)
    # decomposition.trend.plot(figsize=(10,2), title='Trend')
    # plt.show()
    # decomposition.seasonal['2018-01-01':'2019-01-01'].plot(figsize=(10,2), title='Seasonality')
    # plt.show()
    # decomposition.resid.plot(figsize=(10,2), title='Residuals')
    # plt.show()
    return decomposition.seasonal

def plot_data_properties(data, ts_plot_name='Time Series Plot'):
    '''
    Plots various plots
    :param data: Time Series Data, Series, DataFrame
    :param ts_plot_name: Plot name as String
    :return: None
    '''
    plt.figure(figsize=(16,4))
    plt.plot(data)
    plt.title(ts_plot_name)
    plt.ylabel('Price')
    plt.xlabel('Year')
    fig, axes = plt.subplots(1,3,squeeze=False)
    fig.set_size_inches(16,4)
    plot_acf(data, ax=axes[0,0], lags=10)
    plot_pacf(data, ax=axes[0,1], lags=10)
    sns.distplot(data, ax=axes[0,2])
    axes[0,2].set_title("Probability Distribution")
    plt.show()

df = pd.read_csv('data\\ES_weekly.csv', index_col='Date', parse_dates=True)['Settle']
print(df[df.isnull()])
print(df.index.inferred_freq)
log_transformed_data = np.log(df)
# seasonally_diffed_data = log_transformed_data.diff()[1:]
seasonal = plot_seasonal_decompose(df['1998-01-01':], 'multiplicative')
# plot_data_properties(seasonally_diffed_data, 'Log transformed, diff=1 and seasonally differenced data')

seasonal['2018-01-01':'2019-01-01'].plot(figsize=(10,2), title='Seasonality')
plt.show()
print(seasonal['2019-11-01':])