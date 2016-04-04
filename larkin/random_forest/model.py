# coding=utf-8

import pandas as pd
import sklearn.ensemble
import sklearn.grid_search
import sklearn.preprocessing
import sklearn.svm
import sklearn.svm.classes

from larkin.model_config import model_config
from larkin.ts_proc.covar_build import get_covars
from larkin.ts_proc.munge import is_discrete

__author__ = 'David Karapetyan'

nary_thresh = model_config["sampling"]["nary_thresh"]


def _build(endog, weather_history, weather_forecast, cov, gran, params):
    covars = get_covars(endog, weather_history, weather_forecast,
                        cov, gran, "random_forest")

    discrete = is_discrete(endog, nary_thresh)
    if discrete is True:
        rforest = sklearn.ensemble.RandomForestClassifier(**params)

    else:
        rforest = sklearn.ensemble.RandomForestRegressor(**params)

    fit = rforest.fit(covars["x_train"], covars["y_train"])

    return {"fit": fit, "covars": covars}


def predict(endog, weather_history, weather_forecast, cov, gran, params):
    model_items = _build(endog, weather_history, weather_forecast, cov, gran,
                         params)
    fit = model_items["fit"]
    covars = model_items["covars"]

    predicted_series = pd.Series(
        data=fit.predict(covars["x_future"]),
        index=covars["prediction_index"])

    return {
        "prediction": predicted_series,
        "feature_importances": fit.feature_importances_,
        "score": fit.oob_score_
    }
