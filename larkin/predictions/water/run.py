# coding=utf-8

import logging
import logging.config

import larkin.random_forest.model
import larkin.svm.model
from larkin.logging_config import config as log_cfg
from larkin.model_config import model_config
from larkin.predictions.utils import pred_json_conv
from larkin.ts_proc.utils import get_water_ts
from larkin.user_config import user_config
from larkin.weather.mongo import get_history, get_forecast

dbs = user_config["building_dbs"]
buildings = user_config["default"]["buildings"]

cov = model_config["weather"]["cov"]
gran = model_config["sampling"]["granularity"]
params_svr = model_config["svr"]["params"]
params_rfr = model_config["rfr"]["params"]
param_grid = model_config["svr"]["param_search"]["grid"]
cv = model_config["svr"]["param_search"]["cv"]
n_jobs = model_config["svr"]["param_search"]["n_jobs"]
threshold = model_config["svr"]["param_search"]["threshold"]
has_bin_search = model_config["svr"]["param_search"]["has_bin_search"]
gap_threshold = model_config["sampling"]["gap_threshold"]
accuracy = model_config["sampling"]["accuracy"]
order = model_config["sarima"]["order"]
seasonal_order = model_config["sarima"]["seasonal_order"]

# logger setup
logging.config.dictConfig(log_cfg)
logger = logging.getLogger("root")


def main():
    logger.info("Running water prediction:")
    building_preds = {}
    for building in buildings:
        endog = get_water_ts(host=dbs["mongo_cred"]["host"],
                             port=dbs["mongo_cred"]["port"],
                             database=dbs["building_ts_loc"][
                                 "db_name"],
                             username=dbs["mongo_cred"][
                                 "username"],
                             password=dbs["mongo_cred"]["password"],
                             source=dbs["mongo_cred"]["source"],
                             collection_name=dbs["building_ts_loc"][
                                 "collection_name"],
                             building=building,
                             meter_count=2
                             )

        weather_history = get_history(host=dbs["mongo_cred"]["host"],
                                      port=dbs["mongo_cred"]["port"],
                                      source=dbs["mongo_cred"]["source"],
                                      username=dbs["mongo_cred"][
                                          "username"],
                                      password=dbs["mongo_cred"]["password"],
                                      db_name=dbs["weather_history_loc"][
                                          "db_name"],
                                      collection_name=
                                      dbs["weather_history_loc"][
                                          "collection_name"])

        weather_forecast = get_forecast(host=dbs["mongo_cred"]["host"],
                                        port=dbs["mongo_cred"]["port"],
                                        source=dbs["mongo_cred"]["source"],
                                        username=dbs["mongo_cred"][
                                            "username"],
                                        password=dbs["mongo_cred"]["password"],
                                        db_name=dbs["weather_forecast_loc"][
                                            "db_name"],
                                        collection_name=
                                        dbs["weather_forecast_loc"][
                                            "collection_name"])

        pred_forest = larkin.random_forest.model.predict(endog, weather_history,
                                                         weather_forecast, cov,
                                                         gran, params_rfr)
        pred_svr = larkin.svm.model.predict(endog, weather_history,
                                            weather_forecast, cov, gran,
                                            params_svr, param_grid, cv,
                                            threshold, n_jobs, has_bin_search)

        building_preds.update(
                {building: {"svr": pred_svr, "svm": pred_forest}})

    logger.debug(
            "Now printing all building predictions: {}".format(
                    building_preds))
    logger.info("Finished water prediction run successfully.")
    pred_json_conv(building_preds, "water")
    return building_preds


if __name__ == '__main__':
    main()
