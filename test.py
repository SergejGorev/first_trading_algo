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

def mean_abs_pct_error(actual_values, forecast_values):
    err=0
    for i in range(len(forecast_values)):
        err += np.abs(actual_values.values[i] - forecast_values.values[i]/actual_values.values[i])
    return err[0] * 100/len(forecast_values)

# todo eventually change to daily data
df = pd.read_csv('data\\ES_weekly.csv', index_col='Date', parse_dates=True)#['Settle']
test_start_date = '2019-01-01'
test_end_date = df[:]
# todo figure out how to get index of last entry
log_transformed_train_data = np.log(df['Last'].loc[:test_start_date])
log_transformed_test_data = np.log(df['Last'].loc[test_start_date:])
# seasonally_diffed_data = log_transformed_train_data.diff()[10:]
# test_stationarity(seasonally_diffed_data)
# shapiro_normaly_test(seasonally_diffed_data)
# plot_data_properties(seasonally_diffed_data, 'Log transformed, diff=52 and seasonally differenced data')
# decomposition = plot_seasonal_decompose(df['Last'], 'multiplicative')

# best_model, models = best_sarima_model(train_data=log_transformed_train_data,p=range(3),q=range(3),P=range(3),Q=range(3))
# preds_best = np.exp(best_model.predict(start='2019-01-01', dynamic=True, typ='levels'))
# print(f'MAPE{np.round(mean_abs_pct_error(log_transformed_test_data,preds_best),2)}')

agile_model = SARIMAX(endog=log_transformed_train_data,
                      order=(1,1,2),
                      seasonal_order=(1,1,2,52),
                      enforce_invertibility=False).fit()
agile_model.summary()
# todo figure out how to match start date of the index
#just do deactive warnings regarding PyCharm and Numpy
# noinspection PyTypeChecker
agile_model_pred = np.exp(agile_model.predict(start=test_start_date,
                                              end=test_end_date,
                                              dynamic=True,
                                              typ='levels'))
print(f'MAPE{np.round(mean_abs_pct_error(log_transformed_test_data,agile_model_pred),2)}%')
print(f'MAE:{np.round(mean_absolute_error(log_transformed_test_data,agile_model_pred),2)}')

# todo made mistake in train_data. It is just splited original data
def plot_prediciton(training_data,agile_model,agile_model_pred, original_data):
    model_data = training_data.values[1:].reshape(-1) - agile_model.resid[1:]
    model_data = pd.concat((model_data,agile_model_pred))
    plt.figure(figsize=(16,6))
    plt.plot(model_data)
    plt.plot(original_data[1:])
    plt.legend('Model Forecast', 'Original Data')
    plt.show()

plot_prediciton(log_transformed_train_data,agile_model,agile_model_pred, df['Last'].loc[:"2019-01-01"])