# coding=utf-8
from scipy.optimize import brute
from statsmodels.tsa.arima_model import ARIMA


def optimal_order(ts):
    """Outputs optimal Arima order for an input time series.

    :param ts: pandas.core.series.Series
    :return: tuple
    """

    return tuple(
            map(int,
                brute(lambda x: ARIMA(ts, x).fit().aic,
                      ranges=(slice(0, 2, 1),
                              slice(0, 2, 1),
                              slice(0, 2, 1)),
                      finish=None)
                )
    )
