# coding=utf-8
import codecs
import json
import logging
import re
from urllib2 import urlopen

import numpy as np
import pandas as pd
import pytz
from pandas.tseries.offsets import timedelta

import larkin.weather.wet_bulb
from larkin.model_config import model_config

__author__ = "David Karapetyan"

stringcols = ['conds', 'wdire']


def _dtype_conv(df=pd.DataFrame(),
                conds_mapping=model_config["weather"]["conds_mapping"],
                wdire_mapping=model_config["weather"]["wdire_mapping"]):
    """Relabeling of weather underground columns, and conversion of column
    entries to either float or string data types (forecasting models expect
    float entries to have a type signature of 'float')

    :param df: DataFrame
    :param conds_mapping: Dictionary
    Maps original weather underground labels to user-specified labels.
    Used to make weather underground forecast labels match historical data
    labels
    :return: DataFrame
    """
    # next, convert each column to appropriate data type, so that interpolation
    # works properly (will work on type float, but not on generic object

    # fill done different for text vs float columns
    floatcols = df.columns[df.columns.isin(stringcols) == False]
    # convert each column label to appropriate dtype. Convert sentinels
    # (negative numbers) to nan
    for stringcol in stringcols:
        if stringcol in df.columns:
            df[stringcol] = df[stringcol].apply(
                lambda x: str(x) if x != 'N/A' else np.nan)
    for floatcol in floatcols:
        if floatcol in df.columns:
            df[floatcol] = df[floatcol].apply(
                lambda x: float(x) if x != 'N/A' and float(
                    x) > -999 else np.nan)

    # map conditions to uniformly spaced, unique integer values for processing
    # in models, with basic error checking.
    # conds reflects historical conditions, so bottom
    # code will make forecast conds be identical to history conds
    if 'conds' in df.columns:
        df['conds'] = df['conds'].apply(
            lambda x: conds_mapping[x] if x in conds_mapping.keys()
            else np.nan)
    if 'wdire' in df.columns:
        df['wdire'] = df['wdire'].apply(
            lambda x: wdire_mapping[x] if x in wdire_mapping.keys()
            else np.nan)
        df[['conds', 'wdire']] = df[['conds', 'wdire']].fillna(method="bfill")
    return df


def history_pull(city, state, wund_url, date):
    """Weather information is pulled from weather underground at specified
    day

    :param date: datetime object
    Date to pull data for
    :param city: string
    City to pull data for
    :param wund_url: string
    Weather underground account url (with key)
    :param state: string
    State to pull data for
    :return: dataframe
    Weather parameters, indexed by hour
    """

    date_path = 'history_%s%s%s' % (date.strftime('%Y'),
                                    date.strftime('%m'),
                                    date.strftime('%d'))

    city_path = '%s/%s' % (state, city)

    url = wund_url + \
          "%s/q/%s.json" % (date_path, city_path)

    reader = codecs.getreader('utf-8')
    f = urlopen(url)
    parsed_json = json.load(reader(f))
    f.close()
    observations = parsed_json['history']['observations']
    # convert to dataframes for easy presentation and manipulation

    df = pd.DataFrame.from_dict(observations)
    # convert date column to datetimeindex
    dateindex = df.utcdate.apply(
        lambda x: pd.to_datetime(x['pretty'], utc=True))

    dateindex.name = None
    df = df.set_index(dateindex)
    return df


def history_munge(df, gran):
    """For munging history pull from weather underground

    :param df: dataframe
    Weather underground history pull
    :param gran: int
    Resampling granularity
    :return: dataframe
    """
    # drop what we don't need anymore, and set df index
    # dropping anything with metric system
    df_new = df.copy()
    dates = ['date', 'utcdate']
    misc = ['icon', 'metar']
    metric = ['dewptm', 'heatindexm', 'precipm', 'pressurem', 'tempm',
              'vism', 'wgustm',
              'windchillm', 'wspdm']
    df_new = df_new.drop(dates + misc + metric, axis=1)
    column_trans_dict = {
        'heatindexi': 'heatindex', 'precipi': 'precip',
        'pressurei': 'pressure', 'tempi': 'temp',
        'wgusti': 'wgust',
        'windchilli': 'windchill', 'wspdi': 'wspd',
        'visi': 'vis', 'dewpti': 'dewpt'
    }
    df_new = df_new.rename(columns=column_trans_dict)
    df_new = _dtype_conv(df_new)

    # resampling portion
    df_new = df_new.resample(gran).last()
    df_new = df_new.fillna(method="bfill")

    # add wetbulb temperature
    df_new['wetbulb'] = df_new.apply(
        lambda x: larkin.weather.wet_bulb.compute_bulb(
            temp=x['temp'],
            dewpt=x['dewpt'],
            pressure=x['pressure']),
        axis=1)

    return df_new


def forecast_pull(city, state, wund_url):
    """Returns forecasts from now until end of day

     :param city: string
     City portion of city-state pair to pull from weather underground
     :param state: string
     State portion of city-state pair to pull from weather underground
     :return: dataframe of weather parameters, indexed by hour
    """

    city_path = '%s/%s' % (state, city)
    url = wund_url + "hourly/q/%s.json" % city_path
    reader = codecs.getreader('utf-8')
    f = urlopen(url)
    parsed_json = json.load(reader(f))
    f.close()

    df = parsed_json['hourly_forecast']

    # convert to dataframes for easy presentation and manipulation

    df = pd.DataFrame.from_dict(df)
    dateindex = df.FCTTIME.apply(
        lambda x: pd.datetime.fromtimestamp(int(x['epoch']), tz=pytz.utc))
    dateindex.name = None
    df = df.set_index(dateindex)
    return df


def forecast_munge(df, gran, weather_history_munged=None):
    """For munging forecast pull from weather underground

    :param df: dataframe
    Weather underground forecast pull
    :param gran: int
    Resampling granularity
    :return: dataframe
    """
    # toss out metric system in favor of english system
    df_new = df.copy()
    for column in ['windchill', 'wspd', 'temp', 'qpf', 'snow', 'mslp',
                   'heatindex', 'dewpoint', 'feelslike']:
        df_new[column] = df_new[column].apply(
            lambda x: x['english']
        )

        # add columns from forecast data to match weather underground past
        # data pull

        df_new['wdird'] = df_new['wdir'].apply(
            lambda x: x['degrees'])
        df_new['wdire'] = df_new['wdir'].apply(
            lambda x: x['dir'])

    # rename to have name mappings of identical entries in historical and
    # forecast dataframes be the same
    column_trans_dict = {
        'condition': 'conds', 'humidity': 'hum',
        'mslp': 'pressure', 'pop': 'rain',
        'dewpoint': 'dewpt'
    }
    df_new = df_new.rename(columns=column_trans_dict)

    # delete redundant columns
    df_new['conds'] = df_new['wx']
    df_new = df_new.drop(['wx', 'wdir', 'FCTTIME', 'icon', 'icon_url'], axis=1)

    # appropriate data type conversion for columns
    df_new = _dtype_conv(df_new)

    # resampling portion

    df_new = df_new.resample(gran).last()
    df_new = df_new.fillna(method="bfill")

    ###due to resampling and only hourly collection of forecasts by wund,
    # there may be a time gap between weather history and forecast condition
    # bottom fixes this

    forecast_new = pd.Series()
    if weather_history_munged is None:
        logging.warn("You may have a timegap between realtime timeseries"
                     "and predictions. Provide the munged weather history"
                     "dataframe to avoid this")
    else:

        end_history = weather_history_munged.tail(1).index[0]
        begin_forecast = df_new.head(1).index[0]
        time_gap = begin_forecast - end_history
        gran_int = int(re.search(r'\d+', gran).group())
        normal_gap = timedelta(minutes=gran_int)

        if time_gap != normal_gap:
            forecast_new = pd.Series(
                index=pd.date_range(
                    start=end_history + normal_gap,
                    end=begin_forecast - normal_gap,
                    freq=gran))
            forecast_new = forecast_new.append(df_new)
            # fill new na's introduced at top
            forecast_new = forecast_new.fillna(method="bfill")

        else:
            forecast_new = df_new

    # add wetbulb temperature
    forecast_new['wetbulb'] = forecast_new.apply(
        lambda x: larkin.weather.wet_bulb.compute_bulb(
            temp=x['temp'],
            dewpt=x['dewpt'],
            pressure=x['pressure']), axis=1)

    return forecast_new
