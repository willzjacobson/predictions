# coding=utf-8
# TODO temporary var settings--refactor granularity field so that it is int
gran_int = 15
gran_string = str(15) + "min"
seasonality = 60 / gran_int * 24
import numpy as np

model_config = dict(
        sampling={
            'forecast_length': 24,
            'granularity': "15min",
            'nary_thresh': 5,
            'accuracy': '1min',
            'gap_threshold': 2},
        svr={
            'param_search': {
                'cv': 3,
                'grid': {
                    'C': list(np.logspace(
                            base=10,
                            num=20,
                            start=0,
                            stop=5)),
                    'epsilon': [0.1],
                    'gamma': list(np.logspace(
                            base=10,
                            num=30,
                            start=-3,
                            stop=1)),
                    'kernel': ['rbf'],
                },
                'has_bin_search': False,
                'n_jobs': -1,
                'threshold': 0.003},
            'params': {
                'cache_size': 30000,
                'max_iter': -1,
                'shrinking': True,
                'tol': 0.001,
                'verbose': False},
            'scofunc': 'r2',
            # 'mean_absolute_error', 'r2'
        },
        svc={
            'param_search': {
                'cv': 3,
                'grid': {
                    'C': list(np.logspace(
                            base=10,
                            num=20,
                            start=0,
                            stop=5)),
                    'gamma': list(np.logspace(
                            base=10,
                            num=30,
                            start=-3,
                            stop=1)),
                    'kernel': ['rbf'],
                    'class_weight': [None]
                },
                'has_bin_search': False,
                'n_jobs': -1,
                'threshold': 0.003},
            'params': {
                'cache_size': 30000,
                'max_iter': -1,
                'shrinking': True,
                'tol': 0.001,
                'verbose': False},
            'scofunc': 'accuracy'
        },
        weather={
            'conds_mapping': {
                'Clear': 0,
                'Cloudy': 16,
                'Fog': 9,
                'Haze': 3,
                'Heavy Rain': 8,
                'Heavy Snow': 14,
                'Light Freezing Rain': 15,
                'Light Rain': 6,
                'Light Snow': 11,
                'Mist': 13,
                'Mostly Cloudy': 4,
                'Overcast': 5,
                'Partly Cloudy': 2,
                'Rain': 7,
                'Scattered Clouds': 1,
                'Showers': 7,
                'Snow': 12,
                'Unknown': 10},
            'cov': ['wetbulb'],
            'seasons': {
                'fall': [9, 12],
                'spring': [3, 6],
                'summer': [6, 9],
                'winter': [12, 3]},
            'wdire_mapping': {
                'ENE': 6,
                'ESE': 12,
                'East': 15,
                'NE': 5,
                'NNE': 3,
                'NNW': 4,
                'NW': 16,
                'North': 1,
                'SE': 10,
                'SSE': 11,
                'SSW': 13,
                'SW': 8,
                'South': 14,
                'Variable': 0,
                'WNW': 9,
                'WSW': 7,
                'West': 2}},
        arima={
            'order': [1, 1, 0]},
        sarima={
            'order': [1, 1, 0],
            'seasonal_order': [1, 1, 0, 96]
        },
        rfc={
            'params': {
                'n_estimators': 40,
                'criterion': 'gini',
                'max_features': None,  # max_features=n_features
                'n_jobs': -1,
                'oob_score': True,  # use out of bag samples to estimate error
                'verbose': False,
                'class_weight': None  # key parameter to play with
            }
        },
        rfr={
            'params': {
                'n_estimators': 40,
                'criterion': 'mse',
                'max_features': None,  # max_features=n_features
                'n_jobs': -1,
                'oob_score': True,  # use out of bag samples to estimate error
                'verbose': False
            }
        },
    default={
        'debug': False
        }
)
