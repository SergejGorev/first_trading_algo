import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')
from scipy.stats import shapiro

def test_stationarity(data):
    p_val = adfuller(data)[1]
    if p_val >= 0.05:
        print(f'Time Series is not stationary. Adfuller test pvalue={p_val}')
    else:
        print(f'Time Series is stationary. Adfuller test pvalue={p_val}')

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

def plot_seasonal_decompose(data, model):
    '''
    Summary:
    Plots trend, seasonality and residual
    :param data: DataFrame, Series
    :param model: multiplicative or additive
    :return: decomposition(obj): value of statsmodels.tsa.seasonal.seasonal_decompose
    '''
    decomposition = seasonal_decompose(data,model=model)
    decomposition.trend.plot(figsize=(10,2), title='Trend')
    plt.show()
    decomposition.seasonal.plot(figsize=(10,2), title='Seasonality')
    plt.show()
    decomposition.resid.plot(figsize=(10,2), title='Residuals')
    plt.show()
    return decomposition

def shapiro_normaly_test(data):
    p_value = shapiro(data)[1]
    if p_value >= 0.05:
        print("Data follows normal distribution: X~N" + str((np.round(np.mean(data), 3), np.round(np.std(data), 3))))
        print("Shapiro test p_value={}".format(np.round(p_value, 3)))
    else:
        print("Data failed shapiro normality test with p_value={}".format(np.round(p_value, 3)))

def best_sarima_model(train_data,p,q,P,Q,d=1,D=1,s=52):
    best_model_aic = np.Inf
    best_model_bic = np.Inf
    best_model_hqic = np.Inf
    best_model_order = (0,0,0)
    models = []
    for p_ in p:
        for q_ in q:
            for P_ in P:
                for Q_ in Q:
                    try:
                        no_of_lower_metrics = 0
                        model = SARIMAX(endog=train_data,
                                        order=(p_,d,q_),
                                        seasonal_order=(P_,D,Q_,s),
                                        enforce_invertibility=False).fit()
                        models.append(model)
                        if model.aic <= best_model_aic: no_of_lower_metrics+=1
                        if model.bic <= best_model_bic: no_of_lower_metrics+=1
                        if model.hqic <= best_model_hqic: no_of_lower_metrics+=1
                        if no_of_lower_metrics >= 2:
                            best_model_aic = np.round(model.aic,0)
                            best_model_bic = np.round(model.bic,0)
                            best_model_hqic = np.round(model.hqic,0)
                            best_model_order = (p_,d,q_,P_,D,Q_,s)
                            current_best_model = model
                            models.append(model)
                            print('Best model so far: SARIMA' + str(best_model_order)
                                  + f' AIC:{best_model_aic} BIC:{best_model_bic} HQIC:{best_model_hqic}'
                                  + f' resid:{np.round(np.exp(current_best_model.resid).mean(),3)}')
                    except:
                        pass
    print('\n')
    print(current_best_model.summary())
    return current_best_model, models



df = pd.read_csv('data\\ES_weekly.csv', index_col='Date', parse_dates=True)#['Settle']
log_transformed_data = np.log(df['Last'])
seasonally_diffed_data = log_transformed_data.diff()[10:]
# test_stationarity(seasonally_diffed_data)
# shapiro_normaly_test(seasonally_diffed_data)
# plot_data_properties(seasonally_diffed_data, 'Log transformed, diff=52 and seasonally differenced data')
# decomposition = plot_seasonal_decompose(df['Last'], 'multiplicative')

best_model, models = best_sarima_model(train_data=log_transformed_data,p=range(3),q=range(3),P=range(3),Q=range(3))
