# coding=utf-8

import logging

import numpy as np
import pandas as pd
import sklearn.grid_search
import sklearn.preprocessing
import sklearn.svm
import sklearn.svm.classes

from larkin.model_config import model_config
from larkin.ts_proc.covar_build import get_covars
from larkin.ts_proc.munge import is_discrete

__author__ = 'David Karapetyan'

nary_thresh = model_config["sampling"]["nary_thresh"]


def _build(endog, weather_history, weather_forecast, cov, gran, params,
           param_grid, cv, threshold, n_jobs, bin_search):
    """SVM Model Instantiation and Training

    :param params: Dictionary of SVM model parameters
    :param param_grid: Dictionary of C and gamma values
    The C and gamma keys point to lists representing initial grids used to find
    the optimal C and gamma
    :param cv: Number of Stratified K-fold cross-validation folds
    :param threshold: float. Binary search termination criterion.
    Search over grid terminates if difference of next iteration from current
    does not exceed threshold.
    Identifies whether the endogenous variable
    is discrete or takes a continuum of values
    :return: List of objects.
    One contains the fitted model, the other the data
    normalization scaling parameters
    """

    covars = get_covars(endog, weather_history, weather_forecast,
                        cov, gran, "svm")

    discrete = is_discrete(endog, nary_thresh)
    if discrete is True:
        svm = sklearn.svm.SVC(**params)

    else:
        svm = sklearn.svm.SVR(**params)

    # get optimal gamma and c
    if bin_search:
        param_grid_opt = _best_params(endog=covars["y_train"],
                                      features=covars["x_train"],
                                      estimator=svm,
                                      param_grid=param_grid, cv=cv,
                                      n_jobs=n_jobs,
                                      threshold=threshold)
        # refit support vector model with optimal c and gamma
        new_params = params
        new_params["C"] = param_grid_opt["C"]
        new_params["gamma"] = param_grid_opt["gamma"]
        svm.set_params(**new_params)
        # fit the optimal build on covariate set
        # TODO inputs come from svm_dframe prep module

        fit = svm.fit(covars["x_train"], covars["y_train"])
    else:
        if type(svm) == sklearn.svm.classes.SVC:
            scofunc = model_config["svc"]["scofunc"]
        elif type(svm) == sklearn.svm.classes.SVR:
            scofunc = model_config["svr"]["scofunc"]
        else:
            raise ValueError("You have entered an invalid svm. Please use"
                             "an svm of class SVR or SVC")
            # fixed grid search along specified grid
        fit = sklearn.grid_search.GridSearchCV(
                estimator=svm,
                param_grid=param_grid,
                scoring=scofunc,
                cv=cv,
                n_jobs=n_jobs).fit(covars["x_train"], covars["y_train"])
        for item in fit.grid_scores_:
            logging.debug("Printing grid search score: {}".format(item))

        logging.debug("The best parameters are {} with a score of {}".format(
                fit.best_params_, fit.best_score_))


    return {"fit": fit, "covars": covars}


def _best_gamma_fit(endog, features, estimator, c, param_grid_gamma, cv, n_jobs,
                    threshold):
    # base case setup
    # initialization to run while loop below at least once (handling the
    # base case at a minimum)
    params = {"C": [c], "gamma": param_grid_gamma}
    score = threshold
    score_next = 3 * threshold
    fit = None

    if type(estimator) == sklearn.svm.classes.SVC:
        scofunc = model_config["svm"]["disc_scofunc"]
    elif type(estimator) == sklearn.svm.classes.SVR:
        scofunc = model_config["svm"]["cont_scofunc"]
    else:
        raise ValueError("You have entered an invalid estimator. Please use"
                         "an estimator of class SVR or SVC")

    while np.abs(score_next - score) > threshold and score_next > score:
        fit = sklearn.grid_search.GridSearchCV(
                estimator=estimator,
                param_grid=params,
                scoring=scofunc,
                cv=cv,
                n_jobs=n_jobs).fit(features, endog)

        center = fit.best_params_['gamma']
        left = params['gamma'][0]
        right = params['gamma'][-1]
        left_mid = (left + center) / 2
        right_mid = (right + center) / 2
        # check if last element or first element
        # of parameter grid is best. If so, return

        # if left and right is center:
        #     return fit

        # inductive step
        # In the case when right or left equal center, 'set' removes
        # redundant elements
        # sorting done due to weird bug with gridsearch--unsorted
        # grids take longer to process

        left_new_params = {'C': [c],
                           'gamma': sorted({left, left_mid, center})}
        right_new_params = {'C': [c],
                            'gamma': sorted({center, right_mid, right})}

        fit_next_1 = sklearn.grid_search.GridSearchCV(
                estimator=estimator,
                param_grid=left_new_params,
                scoring=scofunc,
                n_jobs=n_jobs).fit(features, endog)

        fit_next_2 = sklearn.grid_search.GridSearchCV(
                estimator=estimator,
                param_grid=right_new_params,
                scoring=scofunc,
                n_jobs=n_jobs).fit(features, endog)

        if fit_next_1.best_score_ <= fit_next_2.best_score_:
            params = right_new_params
            fit_next = fit_next_2
        else:
            params = left_new_params
            fit_next = fit_next_1

        score = fit.best_score_
        score_next = fit_next.best_score_

    return fit


def _best_params(endog, features, estimator, param_grid, cv, n_jobs, threshold):
    """
    Function returning a dictionary of the optimal SVM C and gamma
    parameters

    :param estimator: The scikit-learn model class.
    Example: SVC
    :param param_grid: Dictionary of initial C and gamma grid.
    Optimization is done over this grid using binary search
    :param n_jobs: Number of processors for run
    :param threshold: Binary search termination criterion.
    Search terminates if difference of next iteration from current
    does not exceed threshold.
    :return: Dictionary of optimal C and gamma values for SVM run
    """
    param_grid_gamma = param_grid["gamma"]
    params = []
    scores = []
    for constant in param_grid["C"]:
        fit = _best_gamma_fit(endog=endog,
                              features=features,
                              estimator=estimator,
                              c=constant,
                              param_grid_gamma=param_grid_gamma,
                              cv=cv,
                              n_jobs=n_jobs,
                              threshold=threshold)
        scores.append(fit.best_score_)
        params.append(fit.best_params_)

    ind = np.argmax(scores)

    collated = params
    for (x, y) in zip(collated, scores):
        x["score"] = y
        logging.debug("Parameters: {}".format(x))

    logging.debug("The best parameters are {} with a score of {}".format(
            params[ind], scores[ind]))

    return params[ind]


def predict(endog, weather_history, weather_forecast, cov, gran, params,
            param_grid, cv, threshold, n_jobs, has_bin_search):
    """Time Series Prediciton Using SVM

    :param params: Dictionary of SVM model parameters
    :param param_grid: Dictionary of grid values for svm C and gamma
    :param cv: Number of Stratified K-fold cross-validation folds
    :param threshold: float. Binary search termination criterion.
    Search over grid terminates if difference of next iteration from current
    does not exceed threshold.
    :param n_jobs: Positive integer specifying number of cores for run
    is discrete or takes a continuum of values
    :param has_bin_search: Boolean. Whether or not to use binary search along
    gamma grid for each fixed C
    :return: Series
    """
    model_items = _build(endog, weather_history, weather_forecast, cov, gran,
                         params, param_grid, cv, threshold, n_jobs,
                         has_bin_search)
    fit = model_items["fit"]
    covars = model_items["covars"]

    predicted_series = pd.Series(
            data=fit.predict(covars["x_future"]),
            index=covars["prediction_index"])

    return {"prediction": predicted_series, "params": fit.best_params_,
            "score": fit.best_score_}
