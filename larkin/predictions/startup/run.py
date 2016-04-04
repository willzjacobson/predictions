# coding=utf-8

import logging
import logging.config

import pandas as pd
from joblib import Parallel, delayed

import larkin.random_forest.model
import larkin.svm.model
from larkin.logging_config import config as log_cfg
from larkin.model_config import model_config
from larkin.predictions.utils import pred_json_conv
from larkin.ts_proc.utils import get_startup_ts
from larkin.user_config import user_config
from larkin.weather.mongo import get_history, get_forecast

dbs = user_config["building_dbs"]
all_buildings = user_config["default"]["buildings"]
# present = pd.Timestamp.utcnow()
present = pd.to_datetime("2016-03-23 4:00:00Z", utc=True)
cov = model_config["weather"]["cov"]
gran = model_config["sampling"]["granularity"]
accuracy = model_config["sampling"]["accuracy"]
gap_threshold = model_config["sampling"]["gap_threshold"]
params = model_config["svc"]["params"]
params_rfc = model_config["rfc"]["params"]
param_grid = model_config["svc"]["param_search"]["grid"]
cv = model_config["svc"]["param_search"]["cv"]
n_jobs = model_config["svc"]["param_search"]["n_jobs"]
threshold = model_config["svc"]["param_search"]["threshold"]
has_bin_search = model_config["svc"]["param_search"]["has_bin_search"]
is_debug = user_config["default"]["debug"]
# set up logger
logging.config.dictConfig(log_cfg)
logger = logging.getLogger("root")


def start_time_comp(ts):
    lag_ts_pred = ts - ts.shift(1)
    jumps = lag_ts_pred[lag_ts_pred == 1]
    if len(jumps) == 0:
        raise Exception("The prediction is uniform, indicating an error"
                        "with the model, the data pull, or the db internals.")
    start_time = jumps.between_time('9:00', '15:00').index[0]
    return start_time


def main(date, debug, buildings):
    logger.info("Running startup prediction:")
    all_buildings_preds = {}
    for building in buildings:
        all_building_preds = {}
        weather_history = get_history(
                host=dbs["mongo_cred"]["host"],
                port=dbs["mongo_cred"]["port"],
                source=dbs["mongo_cred"]["source"],
                username=dbs["mongo_cred"][
                    "username"],
                password=dbs["mongo_cred"][
                    "password"],
                db_name=dbs["weather_history_loc"][
                    "db_name"],
                collection_name=
                dbs["weather_history_loc"][
                    "collection_name"])
        weather_forecast = get_forecast(
                host=dbs["mongo_cred"]["host"],
                port=dbs["mongo_cred"]["port"],
                source=dbs["mongo_cred"]["source"],
                username=dbs["mongo_cred"][
                    "username"],
                password=dbs["mongo_cred"][
                    "password"],
                db_name=dbs["weather_forecast_loc"][
                    "db_name"],
                collection_name=dbs["weather_forecast_loc"][
                    "collection_name"],
                date=date)
        endogs = get_startup_ts(
                host=dbs["mongo_cred"]["host"],
                port=dbs["mongo_cred"]["port"],
                db_name=dbs["building_ts_loc"][
                    "db_name"],
                username=dbs["mongo_cred"][
                    "username"],
                password=dbs["mongo_cred"][
                    "password"],
                source=dbs["mongo_cred"]["source"],
                collection_name=
                dbs["building_ts_loc"][
                    "collection_name"],
                building=building
        )
        for key in endogs.keys():
            endogs[key] = endogs[key][endogs[key].index <= date]

        pred_svm = Parallel()(delayed(larkin.svm.model.predict)(
                endog,
                weather_history,
                weather_forecast,
                cov, gran,
                params,
                param_grid,
                cv,
                threshold,
                n_jobs,
                has_bin_search) for endog in endogs.values())

        pred_forest = Parallel()(delayed(larkin.random_forest.model.predict)(
                endog,
                weather_history,
                weather_forecast,
                cov, gran,
                params_rfc) for endog in endogs.values())

        for model_name, pred in zip(["svm", "random_forest"],
                                    [pred_svm, pred_forest]):
            building_preds = {device: pred[i] for i, device in
                              enumerate(endogs.keys())}

            start_time_preds = {
                device: {
                    'time': start_time_comp(pred[i]["prediction"]),
                    'score': pred[i]["score"]
                }
                for i, device in enumerate(endogs.keys())}

            # find name of fan with lowest start up time amongst fans
            start_up_fan = min(
                    start_time_preds, key=lambda k: start_time_preds[k]['time'])

            all_building_preds.update(
                    {
                        model_name: {
                            "ts_predictions": building_preds,
                            "start_time_predictions": start_time_preds,
                            "best_start_time": start_time_preds[start_up_fan]
                        }
                    })

        all_buildings_preds.update({building: all_building_preds})

    logger.debug(
            "Now printing all building predictions: {}".format(
                    all_buildings_preds))
    logger.info("Finished startup prediction run successfully.")

    if debug is False:
        pred_json_conv(all_buildings_preds, "startup")

    return all_buildings_preds


if __name__ == '__main__':
    main(present, is_debug, all_buildings)
