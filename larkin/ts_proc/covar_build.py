# coding=utf-8

import datetime
import re

import sklearn.preprocessing

import larkin.ts_proc.munge
import larkin.weather.mongo
import larkin.weather.wund
from larkin.model_config import model_config
from larkin.ts_proc.munge import munger
import pandas as pd

gap_threshold = model_config["sampling"]["gap_threshold"]
accuracy = model_config["sampling"]["accuracy"]
nary_thresh = model_config["sampling"]["nary_thresh"]


def get_covars(endog, weather_orig, forecast_orig, cov, gran, model_name):
    # get weather information

    if len(endog) == 0:
        raise ValueError("Looks like your training set doesn't go"
                         " back this far into the past. Pass in a later"
                         " date up the stack, and make sure"
                         " you are getting the time series from the db."
                         )
    weather_cond = larkin.weather.wund.history_munge(df=weather_orig,
                                                     gran=gran)[cov]

    forecast_cond = larkin.weather.wund.forecast_munge(
        df=forecast_orig,
        gran=gran,
        weather_history_munged=weather_cond)[cov]

    #########
    # processing for training portion
    #########
    munge_func = munger(endog)
    endog_munged = munge_func(endog)
    endog_filt = larkin.ts_proc.munge.filter_day_season(
        endog_munged,
        day=pd.Timestamp.utcnow().weekday(),
        month=pd.Timestamp.utcnow().month)
    # only include dates (as integers)that are both in features and
    # endog in training
    # of model
    dates = endog_filt.index.intersection(weather_cond.index)

    endog_filt = endog_filt[dates]
    present_features = weather_cond.loc[dates]

    future_features = forecast_cond
    prediction_index = future_features.index

    if model_name in ["svm", "random_forest"]:
        # add column with datetime information, sans year or day (convert
        # time since midnight to minutes)
        present_features = present_features.reset_index()
        future_features = future_features.reset_index()
        #
        # need granularity as integer, to convert seconds to minutes
        gran_int = int(re.findall('\d+', gran)[0])

        for item in [present_features, future_features]:
            item['index'] = item['index'].apply(
                lambda date:
                datetime.timedelta(
                    hours=date.hour,
                    minutes=date.minute).total_seconds() / gran_int
            )

    scaler = sklearn.preprocessing.MinMaxScaler().fit(present_features)
    present_features_scaled = scaler.transform(present_features)

    x_train = present_features_scaled
    y_train = endog_filt
    x_future = scaler.transform(future_features)

    return {
        "y_train": y_train,
        "x_train": x_train,
        "x_future": x_future,
        "prediction_index": prediction_index,
        "scaler": scaler
    }
