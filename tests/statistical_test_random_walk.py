from __future__ import print_function
import pandas as pd
from numpy import cumsum, log, polyfit, sqrt, std, subtract
from numpy.random import randn
import statsmodels.tsa.stattools as ts

df = pd.read_csv('data\\ES.csv', index_col='Date', parse_dates=True)

# print(ts.adfuller(df['Last'],1))

def hurst(ts):
    '''
    :param ts:
    :return: Returns the Hurst Exponent of the time series vector ts
    '''
    # Create the range of lag values
    lags = range(2, 100)

    # Calculate the array of the variances of the lagged differences
    tau = [sqrt(std(subtract(ts[lag:], ts[:-lag]))) for lag in lags]

    # Use a linear fit to estimate the Hurst Exponent
    poly = polyfit(log(lags), log(tau), 1)

    # Returns a Horst Exponent from the polyfit output
    return poly[0]*2.0

# Create a Geometric Brownian Motion (GBM = Random Walk), Mean-Reverting and Trending Series
gbm = log(cumsum(randn(100000))+1000)
mr = log(randn(100000)+1000)
tr = log(cumsum(randn(100000)+1)+1000)

# Output of the Hurst Exponent for each of the above series
# and the price of ES for the ADF test above
print(f'Hurst(GBM): {hurst(gbm)}')
print(f'Hurst(MR): {hurst(mr)}')
print(f'Hurst(TR): {hurst(tr)}')
print(f'Hurst(ES): {hurst(df["Last"].values)}')

