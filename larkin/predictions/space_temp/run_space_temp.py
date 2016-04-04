# coding=utf-8

__author__ = 'ashishgagneja'

"""
driver for generating start-time using a ARIMA model for space
temperature data
"""

import logging

import dateutil.relativedelta as relativedelta

import larkin.sarima.model
import larkin.ts_proc.munge
import larkin.ts_proc.utils
from larkin import model_config
from larkin import user_config

cfg = dict(user_config.user_config, **model_config.model_config)

buildings = cfg['default']['buildings']

# iterate over all buildings
for building in buildings:

    bldg_params = cfg['default'][building]
    building_dbs = cfg['building_dbs']
    weather_params = cfg['weather']
    arima_params = cfg['arima']
    granularity = cfg['sampling']['granularity']

    kw_args = dict(building_dbs['mongo_cred'],
                   **building_dbs['building_ts_loc'])

    predictions = []
    for floor_quadrant in bldg_params['floor_quadrants']:
        floor, quad = floor_quadrant

        # get space temp time series
        ts = larkin.ts_proc.utils.get_parsed_ts_new_schema(building=building,
                                                           devices='Space_Temp',
                                                           floor=str(floor),
                                                           quad=quad,
                                                           **kw_args)

        pred_dt = ts.index[-1] - 2 * relativedelta.relativedelta(days=1)
        print(pred_dt)

        # invoke model
        forecast, std_err, conf_int = larkin.sarima.model.start_time(
                ts,
                weather_params['h5file'],
                weather_params['weather_history_loc'],
                weather_params['weather_forecast_loc'],
                arima_params['order'],
                granularity,
                str(pred_dt))

        logging.debug("forecast: %s" % forecast)
        logging.debug("std err: %s" % std_err)
        logging.debug("confidence interval: %s" % conf_int)
