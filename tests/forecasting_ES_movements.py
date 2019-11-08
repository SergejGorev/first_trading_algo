from __future__ import print_function

import datetime
import numpy as np
import pandas as pd
import sklearn

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from sklearn.metrics import confusion_matrix
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis as QDA
from sklearn.svm import LinearSVC, SVC

dir_path = 'data\\'

def create_lagged_series(symbol, start_date=None, end_date=None, lags=5):
    '''
    This creates a Pandas DataFrame object that stores the returns of the closing price of
    a futures continuous contract, along with a number of lagged returns from the prior
    trading days. Trading Volume, as well as the Direction
    from the previous day, are also included.
    :param symbol: Market as Pandas DataFrame (in our case futures)
    :param start_date: start of df
    :param end_date: end of df
    :param lags: number of lagged returns from prior trading days(lags default to 5)
    :return: DataFrame
    '''

    # Read to ts
    path = f'{dir_path}{symbol}.csv'
    ts = pd.read_csv(path, index_col='Date', parse_dates=True).loc[start_date:end_date]

    # Create the new lagged DataFrame
    tslag = pd.DataFrame(index=ts.index)
    tslag['Today'] = ts['Last']
    tslag['Volume'] = ts['Volume']

    # Create the shifted lag series of prior period close values
    for i in range(0, lags):
        tslag[f'Lag{str(i+1)}'] = ts['Last'].shift(i+1)

    # Create the returns DataFrame
    tsret = pd.DataFrame(index=tslag.index)
    tsret['Today'] = tslag['Today'].pct_change()*100.0
    tsret['Volumne'] = tslag['Volume']

    # If any of the values of percentage returns = 0, set the to a small number
    # in order to stop issues with QDA model in Scikit-Lern
    for i,x in enumerate(tsret['Today']):
        if (abs(x) < 0.0001):
            tsret['Today'][i] = 0.0001

    # Create the lagged percentage returns columns
    for i in range(0, lags):
        tsret[f'Lag{str(i + 1)}'] = \
        tslag[f'Lag{str(i + 1)}'].pct_change()*100.0

    # Create "Direction" Column (+1 or -1) indicating an up/down day
    tsret['Direction'] = np.sign(tsret['Today'])
    if start_date is None:
        pass
    else:
        tsret = tsret[tsret.index >= start_date]

    return tsret

if __name__ == "__main__":
    # Create a lagged series of a Market
    snpret = create_lagged_series('ES', lags=5)
    snpret = snpret[snpret['Lag5'].notnull()]
    print(snpret)
    # Use the prior two days of return as predictor
    # values, with direction as the response
    # Thus we are implicitly stating to the classifier that the further lags are of less predictive value

    X = snpret[['Lag1', 'Lag2']]
    y = snpret['Direction']

    # The test data is split into two parts: Before and after 1st Jan 2019.
    start_test = datetime.datetime(2019,1,1)

    # Create training and test sets
    X_train = X[X.index < start_test]
    X_test = X[X.index >= start_test]
    y_train = y[y.index < start_test]
    y_test = y[y.index >= start_test]

    # Create the (parametrised) models
    print('Hit Rates/Confusion Matrices:\n')
    models = [('LR', LogisticRegression()),
              ('LDA', LDA()),
              ('QDA', QDA()),
              ('LSVC', LinearSVC()),
              ('RSVM', SVC(
                  C=1000000.0, cache_size=200, class_weight=None,
                  coef0=0.0, degree=3, gamma=0.0001, kernel='rbf',
                  max_iter=-1, probability=False, random_state=None,
                  shrinking=True, tol=0.001, verbose=False)
               ),
              ('RF', RandomForestClassifier(
                  n_estimators=1000, criterion='gini',
                  max_depth=None, min_samples_split=2,
                  min_samples_leaf=1, max_features='auto',
                  bootstrap=True, oob_score=False, n_jobs=1,
                  random_state=None, verbose=0)
               )]

    # Iterate through the models
    for m in models:
        # Train each of the models on the training set
        m[1].fit(X_train, y_train)

        # Make an array of predictions on the test set
        pred = m[1].predict(X_test)

        # Output the hit-rate and the confusion matrix for each model
        print(f'{m[0]}:\n{round(m[1].score(X_test, y_test),3)}')
        print(f'{confusion_matrix(pred, y_test)}\n')