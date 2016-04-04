# coding=utf-8
import pandas as pd
import pymongo
import pytz
from bson.objectid import ObjectId
from dateutil.relativedelta import relativedelta
from joblib import Parallel, delayed

import larkin.weather.wund
from larkin.user_config import user_config

refresh_rate = user_config["building_dbs"]["wund_cred"]["refresh_rate"]
def _forecast_push(df, host, port, source, username, password,
                   db_name, collection_name):
    """
    Get all observation data with the given building, device and system
    combination from the database

    :param df: pd.DataFrame
        Dataframe to push to mongo_cred
    :param host: string
        database server name or IP-address
    :param db_name: string
        name of the database on server
    :param collection_name: string
        collection name to use

    :return: None
    """

    with pymongo.MongoClient(host=host, port=port) as conn:
        conn[db_name].authenticate(username, password, source=source)
        collection = conn[db_name][collection_name]

        df.index.name = 'time'
        # wund forecasts update hourly, so these labels will be unique
        first_date_in_ts = df.index[0]
        readings = df.reset_index().to_dict("records")

        # don't need to check for existence of document--guaranteed not to exist
        # for each run of model, due to 'date = pd.Timestamp.utcnow()'
        collection.insert({
            "weather_host": "Weather Underground",
            "date": first_date_in_ts,
            "readings": readings,
            "units": "us"
        })


def _mongo_history_push(df, host, port, source, db_name, username, password,
                        collection_name):
    with pymongo.MongoClient(host=host, port=port) as conn:
        conn[db_name].authenticate(username, password, source=source)
        collection = conn[db_name][collection_name]
        df.index.name = 'time'
        # don't have to check if collection exists, due to upsert below
        # this helper function is only pushing dates that don't exist in the db,
        # due to checking in calling function. Hence, using upsert should not
        # cost additional computation power vs just an insert
        bulk = collection.initialize_unordered_bulk_op()
        for date in pd.Series(df.index.date).unique():
            readings = df.loc[
                       date:date + relativedelta(days=1)].reset_index().to_dict(
                "records")
            daytime = pd.Timestamp(date)
            bulk.find({"date": daytime}).upsert().update(
                {
                    "$set": {
                        "weather_host": "Weather Underground",
                        "date": daytime,
                        "readings": readings,
                        "units": "us"
                    }
                })
        bulk.execute()


def forecast_update(city, state, wund_url, host, port, source, username,
                    password, db_name, collection_name):
    data = larkin.weather.wund.forecast_pull(city=city, state=state,
                                             wund_url=wund_url)
    _forecast_push(data, host=host, port=port, source=source,
                   username=username, password=password, db_name=db_name,
                   collection_name=collection_name)


def history_update(city, state, tz, wund_url, parallel, host, port, source,
                   username, password, db_name, collection_name, cap):
    """Pull archived weather information

    Weather information is pulled from weather underground from end of
    prescriptive weather database date to today, then added to
    weather database

    :param wund_url:
    :param city: string
    City portion of city-state pair to pull from weather underground
    :param state: string
    State portion of city-state pair to pull from weather underground
    Location of HDFS archive on disk
    Name of weather dataframe in archive_location HDFS store
    :param cap: int.
    Cap for number of WUnderground pulls, due to membership
    restrictions
    :param parallel: Boolean.
    Whether to process in parallel
    Resampling granularity
    Whether or not to munge wunderground pulled data
    :return: dataframe
    Weather underground history data, indexed with granularity gran
    """

    weather_data = get_history(host=host, port=port, source=source,
                               db_name=db_name, username=username,
                               password=password,
                               collection_name=collection_name,
                               )

    # start is beginning of day for last entry in weather_data
    # we toss out any times already existing between start and end of
    # day in archive weather_data, in order for concat below to run without
    # indices clashing

    # must be very careful to convert all our utc times to local for this
    # section, as weather underground doesn't allow us to pass tz in uri,
    # uri is inferred from city/state combo that is passed in uri

    tz_obj = pytz.timezone(tz)

    # end time is same for both conditions, but start changes
    # depending on whether db is populated or not
    end = pd.Timestamp.utcnow().tz_convert(tz_obj).date()
    if len(weather_data) == 0:
        start = pd.Timestamp.utcnow().tz_convert(tz_obj).date()\
                - relativedelta(years=4)
        weather_data = pd.DataFrame()
    else:
        if not isinstance(weather_data, pd.DataFrame):
            raise ValueError("History pull as dataframe failed")
        start = weather_data.index[-1].date()

    # if start == end:
    #     logging.warn(
    #         "Running weather update too often. No weather data gap between"
    #         " last weather date pulled and current time")
    #     return
    interval = pd.date_range(start, end)
    wdata_days_comp = weather_data[:start]

    if parallel:
        frames = Parallel(n_jobs=-1)(
            delayed(larkin.weather.wund.history_pull)(
                city=city, state=state,
                wund_url=wund_url,
                date=date)
            for date in interval[:cap])
    else:
        frames = [larkin.weather.wund.history_pull(
            city=city, state=state,
            wund_url=wund_url, date=date)
                  for date in interval[:cap]]

    weather_update = pd.concat(frames)
    archive = pd.concat([wdata_days_comp, weather_update])

    if isinstance(weather_update, pd.DataFrame) \
            and isinstance(archive, pd.DataFrame):

        # check for duplicate entries from weather underground, and delete
        # all except one. Unfortunately, drop_duplicates works only for column
        # entries, not timestamp row indices, so...
        archive = archive.reset_index().drop_duplicates('index').set_index(
            'index')
        # push to mongo_cred. Mongo upsert checks if dates already exist,
        # and if they don't, new items are pushed
        _mongo_history_push(archive,
                            host=host,
                            port=port,
                            source=source,
                            username=username,
                            password=password,
                            db_name=db_name,
                            collection_name=collection_name
                            )
    else:
        raise ValueError("Parallel concatenation of dataframes failed")


def get_history(host, port, source, db_name, username, password,
                collection_name):
    """

    :param host:
    :param port:
    :param source:
    :param db_name:
    :param username:
    :param password:
    :param collection_name:
    :return: DataFrame
    """
    whist = []
    with pymongo.MongoClient(host=host, port=port) as conn:
        conn[db_name].authenticate(username, password, source=source)
        collection = conn[db_name][collection_name]
        for data in collection.find():
            reading = data['readings']
            whist.append(reading)

    if len(whist) == 0:
        return whist
    else:
        # convert list of lists of dictionaries to list of dictionaries
        whist = [j for i in whist for j in i]
        whist = pd.DataFrame(whist)
        whist.set_index('time', inplace=True)
        whist = whist.sort_index()

        # key step--must localize to UTC uniformly across suite
        whist = whist.tz_localize('UTC')
        return whist


def get_forecast(host, port, source, db_name, username, password,
                 collection_name, date):
    # forecasts are always pushed after time that whole suite starts running
    # so implementation below is correct, and will result in us
    # being able to capture forecast and archive data used by operator in past
    # when in debug mode in present

    date_lb = date - pd.Timedelta(refresh_rate)
    date_ub = date + pd.Timedelta(refresh_rate)
    with pymongo.MongoClient(host=host, port=port) as conn:
        conn[db_name].authenticate(username, password, source=source)
        collection = conn[db_name][collection_name]

        for data in collection.find({
            "_id":
                {
                    "$gte": ObjectId.from_datetime(
                        date_lb),
                    "$lte": ObjectId.from_datetime(
                        date_ub)
                }
        }).sort(
            "_id", pymongo.ASCENDING):
            reading = data['readings']
            wfore = pd.DataFrame(reading)
            if len(wfore) == 0:
                raise ValueError("An appropriate forecast for the passed"
                                 "date does not exist in the database. Please"
                                 "pass another date, and check to make sure"
                                 "the database is functioning correctly.")
            else:
                wfore.set_index('time', inplace=True)
                wfore = wfore.sort_index()
                wfore = wfore.tz_localize('UTC')
                return wfore
