import logging
import logging.config
import string
import traceback

import pandas as pd

import larkin.predictions.electric.run as erun
import larkin.predictions.occupancy.run as orun
import larkin.predictions.startup.run as srun
import larkin.predictions.water.run as wrun
from larkin.logging_config import config as log_cfg
from larkin.user_config import user_config

__author__ = 'davidkarapetyan'
all_buildings = user_config["default"]["buildings"]
present = pd.Timestamp.utcnow()
logging.config.dictConfig(log_cfg)
logger = logging.getLogger("root")


def select_prediction(kind):
    if kind == "startup":
        return srun.main
    elif kind == "water":
        return wrun.main
    elif kind == "occupancy":
        return orun.main
    elif kind == "electric":
        return erun.main
    else:
        raise ValueError(
                "Invalid building feature kind to predict. "
                "Please enter a different "
                "kind.")


def main(date, debug, buildings, kinds):
    # update weather
    # try:
    #     weather_run.main()
    # except (RuntimeError, TypeError, NameError):
    #     logger.critical("Weather update failed. Predictions"
    #                     " may end up being very off due to usage"
    #                     " of non-current weather data")
    for kind in kinds:
        try:
            select_prediction(kind)(date, debug, buildings)
        except (RuntimeError, TypeError, NameError):
            logger.error(traceback.format_exc())
            logger.critical(string.capwords(kind) + " prediction failed.")


if __name__ == "__main__":
    main(date=present, debug=True, buildings=all_buildings,
         kinds=["startup"])
