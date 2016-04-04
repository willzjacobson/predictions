import logging
import logging.config
import os

import pandas as pd

from larkin.logging_config import config as log_cfg

logging.config.dictConfig(log_cfg)
logger = logging.getLogger("root")


def pred_json_conv(pred_data, pred_type):
    try:
        home = os.path.expanduser('~')
        json_dir = home + "/.larkin/jsons/"
        pred_dir = json_dir + pred_type
        # if directory doesn't exist, create it
        if not os.path.isdir(pred_dir):
            os.makedirs(pred_dir)
        date = pd.Timestamp.utcnow().isoformat()
        file_name = pred_dir + "/predictions_" + "{}".format(date) + ".json"
        # write results
        pd.DataFrame(pred_data).to_json(path_or_buf=file_name,
                                        date_format='iso')
        logger.info(
            "I've written the " + pred_type + " prediction output to json.")
    except (RuntimeError, TypeError, NameError):
        logger.critical("Failed to write results to json.")
