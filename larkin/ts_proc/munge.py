# coding=utf-8


__author__ = 'David Karapetyan'

import datetime

import pandas as pd

from larkin.model_config import model_config

gap_threshold_ = model_config["sampling"]["gap_threshold"]
accuracy_ = model_config["sampling"]["accuracy"]
nary_thresh_ = model_config["sampling"]["nary_thresh"]
gran_ = model_config["sampling"]["granularity"]


def is_discrete(df, nary_thresh):
    if df.nunique() < nary_thresh:
        return True
    else:
        return False


def gap_resamp(df, nary_thresh, gap_threshold, accuracy, gran):
    """For cleaning incoming data, and extracting relevant fields

    :param df: pd.Dataframe
    :param nary_thresh: int. Number of non-unique entries before
    time series is classed as continuous
    :param gap_threshold: int. Length of data gap (in hours) we are
    allowed to interpolate over
    :param accuracy: String. Resampling fineness, relative to the original data.
    For example, "10:16:00 -> 10:15:00" would be a resampling accuracy of
    1min
    :param gran: Resampling granularity. For converting data to final
    resampling rate

    :return: pd.DataFrame. Original DataFrame, interpolated over and resampled,
     with the exception
    """
    # subset out relevant columns

    longest_allowed_gap = datetime.timedelta(hours=gap_threshold)

    # find dates with gaps less than threshold, and resample
    # not doing this on the index directly because shift operator doesn't
    # work on it as expected
    bool_arr = (df.reset_index()['index'] - df.reset_index()['index'].shift()
                ) <= longest_allowed_gap
    bool_arr[0] = True  # shifting eliminated first element, so re-add it
    dates_less_thresh = df.index[bool_arr]

    if (len(dates_less_thresh) / float(len(df.index))) < 0.5:
        raise ValueError("Investigate the data: it has too many gaps")

    dates_le_resamp = pd.Series(
            index=dates_less_thresh).resample(accuracy).index

    # resampling step, where we are careful to only fill NAs via interpolation
    # for gaps less than threshold. No filling for binary data, i.e.
    #  Process nary data different than continuous data

    if is_discrete(df, nary_thresh):
        df_thresh_gran = df.resample(rule=gran).first().dropna()

    else:
        df_thresh = df.resample(rule=accuracy).interpolate()[dates_le_resamp]
        # resample at granularity, and interpolate to fill
        # possible NAs (all of which
        # will again have gaps less than threshold
        df_thresh_gran = df_thresh.resample(rule=gran).first().interpolate()

    return df_thresh_gran


def ts_day_pos(ts, day, time, start, end, freq):
    """Returns slice of input time series

    Time series subset consists of all points at a specific time between
    start and end dates, and sampled with an input frequency

    :param ts: pandas.core.series.Series
    :param day: int
    Day of week
    :param time: datetime.datetime
    Time of day. Defaults to None
    :param start: datetime.datetime
    :param end: datetime.datetime
    :param freq: frequency alias
    :return: pandas.core.series.Series
    """
    temp = ts[pd.date_range(start=start, end=end, freq=freq)]
    temp = temp[temp.index.weekday == day]

    if time is None:
        return temp
    else:
        return temp.at_time(time)


def filter_three_std(ts):
    perc = [.003, .997]
    stats = ts.describe(percentiles=perc)
    low, high = stats['0.3%'], stats['99.7%']
    return ts[ts.between(low, high)]


def filter_day_season(ts, day, month):
    seasons = model_config["weather"]["seasons"]
    month_range = (0, 0)

    for value in seasons.values():
        if value[0] % 12 < month <= value[1] % 12:
            month_range = value

    # filter by day and season
    ts_filt = ts[((ts.index.weekday == day) &
                  (ts.index.month > month_range[0] % 12) &
                  (ts.index.month <= month_range[1] % 12)
                  )]
    return ts_filt


def electricity_spike_munge(ts):
    # temporary code--mongo guys to update db
    filtered = ts[~ts.index.duplicated(keep='first')].dropna()
    # take care of padding guys were doing on mongo, and 0 like values
    # in data
    filtered = filtered[filtered > 0]

    # system testing up to 2012-10-26; cut data up to then
    filtered = filtered['2012-10-26 18:00:00':]
    filtered = filtered[filtered < 15000]
    # filtered = filtered.groupby(
    #         filtered.index.weekofyear).apply(
    #         filter_three_std)
    # filtered = filtered.reset_index(level=0, drop=True)
    filtered = gap_resamp(
            filtered, nary_thresh_, gap_threshold_, accuracy_,
            gran_)

    return filtered

    # find all dates between ith and i+1th spike that are greater than
    # percentage
    # change from date reading at i-1 value (for example, could have multiple
    # readings at a spike level--want to excise these


def occupancy_spike_munge(ts):
    # temporary code--mongo guys to update db
    filtered = ts[~ts.index.duplicated(keep='first')].dropna()
    # take care of padding guys were doing on mongo, and 0 like values
    # in data
    # random zeroes all over the place
    filtered = filtered[filtered > 0]

    # system testing up to 2012-10-26; cut data up to then
    filtered = filtered['2013-05-23 07:30:00':]
    # filtered = filtered.groupby(
    #         filtered.index.date).apply(
    #         lambda df: df.drop_duplicates(keep=False))
    # filtered = filtered.reset_index(level=0, drop=True)

    filtered = gap_resamp(
            filtered, nary_thresh_, gap_threshold_, accuracy_,
            gran_)

    return filtered

    # find all dates between ith and i+1th spike that are greater than
    # percentage
    # change from date reading at i-1 value (for example, could have multiple
    # readings at a spike level--want to excise these


def startup_munge(ts):
    def basic_filt(x):
        if x == "active":
            return 1
        elif x == "inactive":
            return 0
        else:
            return x

    ts_munged = ts.apply(basic_filt)
    ts_munged = gap_resamp(
            ts_munged, nary_thresh_, gap_threshold_, accuracy_,
            gran_)
    return ts_munged


def water_munge(ts):
    filt = ts['2015-12-01':]
    ts_munged = gap_resamp(
            filt, nary_thresh_, gap_threshold_, accuracy_,
            gran_)
    return ts_munged


def munger(ts):
    if ts.name == 'startup':
        return startup_munge
    elif ts.name == 'occupancy':
        return occupancy_spike_munge
    elif ts.name == 'electric':
        return electricity_spike_munge
    elif ts.name == 'water':
        return water_munge
