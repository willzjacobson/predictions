# coding=utf-8
# import IPython.parallel

# rc = IPython.parallel.Client()
# dview = rc[:]
# dview.block = True

# with dview.sync_imports():
import pymongo

# from statsmodels.tsa.statespace.sarimax import SARIMAX
# import seaborn as sns
import pandas as pd
# sns.set()
import pytz


def _construct_device_sum_dframe(ts_lists, value_lists):
    """
    Construct a pandas DataFrame using the time series data on individual
    meter can compute the total instantaneous usage

    :param ts_lists: list of lists
        list of list of timestamps
    :param value_lists: list of lists
        list of list of data corresponding to the timestamps list in the same
        ordinal position in ts_lists

    :return: pandas DataFrame
    """

    master_df = pd.DataFrame()

    # error checks
    if len(ts_lists) != len(value_lists):
        raise ValueError('array lengths must match')
    if not len(ts_lists):
        return master_df

    # insert column data
    for i, ts_list in enumerate(ts_lists):
        master_df = master_df.join(pd.DataFrame(data=value_lists[i],
                                                index=ts_list,
                                                columns=[str(i + 1)]).dropna(),
                                   how='outer')

    return master_df.sum(axis=1).reset_index().drop_duplicates(
            subset='index').set_index('index').sort_index()


def get_electric_ts(host, port, database, username, password, source,
                    collection_name, building, meter_count):
    """ retrieves all available electric data from all meters and sums up
    to get total electric usage time series

    :param host: string
        database server name or IP-address
    :param port: int
        database port number
    :param database: string
        name of the database on server
    :param username: string
        database username
    :param password: string
        database password
    :param source: string
        source database for authentication
    :param collection_name: string
        database collection name to query
    :param building: string
        database building_id identifier
    :param meter_count: int
        number of distinct meters that need to be summed up

    :return: pandas Series
    """
    devices, device_groups = [], {}
    for meter_num in range(1, meter_count + 1):
        meters_t = ["Elec-M%d" % meter_num,
                    "Electric_Meter_%d^Avg_Rate" % meter_num]
        for meter_t in meters_t:
            device_groups[meter_t] = meter_num - 1
        devices.extend(meters_t)

    ts = get_devices_sum_ts(host, port, database, username, password,
                            source, collection_name, building, devices,
                            'Electric_Utility',
                            device_groups)
    ts.name = 'electric'
    return ts


def get_water_ts(host, port, database, username, password, source,
                 collection_name, building, meter_count):
    """ retrieves all available water data from all meters and sums up
    to get total water usage time series

    :param host: string
        database server name or IP-address
    :param port: int
        database port number
    :param database: string
        name of the database on server
    :param username: string
        database username
    :param password: string
        database password
    :param source: string
        source database for authentication
    :param collection_name: string
        database collection name to query
    :param building: string
        database building_id identifier
    :param meter_count: int
        number of distinct meters that need to be summed up

    :return: pandas Series
    """
    devices, device_groups = ['LevelAToday', 'LevelCToday'], {}
    for meter_num in range(1, meter_count + 1):
        device_groups[devices[meter_num - 1]] = meter_num - 1

    ts = get_devices_sum_ts(host, port, database, username, password,
                            source, collection_name, building, devices,
                            'Water_Demand', device_groups)
    ts.name = 'water'
    return ts


def get_occupancy_ts(host, port, db_name, username, password, source,
                     collection_name,
                     building):
    ts = get_parsed_ts_new_schema(host, port, db_name, username, password,
                                  source,
                                  collection_name,
                                  building, devices="Occupancy",
                                  systems="Occupancy")
    ts.name = "occupancy"
    return ts


def get_startup_ts(host, port, db_name, username, password, source,
                   collection_name,
                   building):
    dev_labels = (1, 2, 7, 8)
    sys_labels = dev_labels
    devices = ["S" + str(num) + "-SupplyFanStatus" for num in dev_labels]
    systems = ["S" + str(num) for num in sys_labels]
    all_series = {}
    for device, system in zip(devices, systems):
        ts = get_parsed_ts_new_schema(
                host, port, db_name, username, password,
                source,
                collection_name,
                building, device, system)
        ts.name = 'startup'
        all_series.update({device: ts})
    return all_series


def get_devices_sum_ts(host, port, database, username, password, source,
                       collection_name, building, devices, systems,
                       device_groups):
    """ retrieves all available electric data from all meters and sums up
    to get total electric usage time series

    :param host: string
        database server name or IP-address
    :param port: int
        database port number
    :param database: string
        name of the database on server
    :param username: string
        database username
    :param password: string
        database password
    :param source: string
        source database for authentication
    :param collection_name: string
        database collection name to query
    :param building: string
        database building_id identifier
    :param devices: string or iterable
        device name(s) for identifying time series
    :param systems: string or iterable
        system name(s) for identifying time series
    :param device_groups: dict
        mapping to enable devices to be grouped together

    :return: pandas Dataframe
    """

    ts_lists, value_lists = [], []
    for j in range(0, len(device_groups)):
        ts_lists.append([])
        value_lists.append([])

    device_data = get_device_ts_new_schema(host, port, database, username,
                                           password, source,
                                           collection_name,
                                           building, devices, systems)

    for device, data in device_data.iteritems():
        group = device_groups[device]
        ts_lists[group].extend(data[0])
        value_lists[group].extend(data[1])

    return _construct_device_sum_dframe(ts_lists, value_lists).tz_localize(
            pytz.utc)[0]


def get_parsed_ts_new_schema(host, port, db_name, username, password,
                             source, collection_name, building, devices,
                             systems=None, floor=None, quad=None):
    """Fetch all available timeseries data from database

    :param host: string
        database server name or IP-address
    :param port: int
        database port number
    :param db_name: string
        name of the database on server
    :param username: string
        database username
    :param password: string
        database password
    :param source: string
        source database for authentication
    :param collection_name: string
        collection name to use
    :param building: string
        building identifier
    :param devices: string or iterable
        device name(s) for identifying time series
    :param systems: string or iterable
        system name(s) for identifying time series
    :param floor: string
        floor identifier
    :param quad: string
        quadrant identifier

    :return: pandas DataFrame
        occupancy time series data
    """

    device_data = get_device_ts_new_schema(host, port, db_name, username,
                                           password, source, collection_name,
                                           building, devices, systems,
                                           floor=floor, quad=quad)
    if not hasattr(devices, '__iter__'):
        devices = [devices]
    ts_list, val_list = [], []
    for device in devices:
        ts_list.extend(device_data[device][0])
        val_list.extend(device_data[device][1])

    obs_df = pd.DataFrame({'obs': val_list}, index=ts_list).dropna()

    # drop missing values, set timestamp as the new index and sort by index
    # some duplicates seen in SIF steam data
    return obs_df.reset_index().drop_duplicates(subset='index').set_index(
            'index').sort_index().tz_localize(pytz.utc)['obs']


def get_device_ts_new_schema(host, port, database, username, password, source,
                             collection_name, building, devices, systems=None,
                             floor=None, quad=None):
    """
    Get all observation data with the given building, devices and systems
    combination from the database

    :param host: string
        database server name or IP-address
    :param port: int
        database port number
    :param database: string
        name of the database on server
    :param username: string
        database username
    :param password: string
        database password
    :param source: string
        source database for authentication
    :param collection_name: string
        database collection name
    :param building: string
        building identifier
    :param devices: string or iterable
        device name(s) for identifying time series
    :param systems: string or iterable
        system name(s) for identifying time series
    :param floor: string
        floor identifier
    :param quad: string
        quadrant identifier

    :return: device-indexed dictionary with  a list of lists of timestamps
    followed by a list of values
    """

    with pymongo.MongoClient(host, port) as conn:

        conn[database].authenticate(username, password, source=source)
        collection = conn[database][collection_name]

        device_data = {}

        query = {"building": building}
        # there may be one or more devices to match
        if hasattr(devices, '__iter__'):
            query['device'] = {'$in': devices}
            for device in devices:
                device_data[device] = [[], []]
        else:
            query['device'] = devices
            device_data[devices] = [[], []]

        # handle optional arguments
        # systems is optional, for example for steam data
        for field, value in {'system': systems, 'floor': floor,
                             'quadrant': quad}.iteritems():
            if value:
                # there may be one or more systems names to match
                if hasattr(value, '__iter__'):
                    query[field] = {'$in': value}
                else:
                    query[field] = value

        for doc in collection.find(query):

            device = doc['device']
            readings = doc['readings']
            zipped = [(x['time'], x['value']) for x in readings
                      if x['time'] is not None and 'value' in x]

            if len(zipped):
                ts_list_t, val_list_t = zip(*zipped)
                device_str = str(device)
                device_data[device_str][0].extend(ts_list_t)
                device_data[device_str][1].extend(val_list_t)

    return device_data
