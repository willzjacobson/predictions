# coding=utf-8
import functools

import joblib
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from statsmodels.tsa.arima_model import ARIMA

from larkin.ts_proc.munge import filter_two_std


def actual_vs_prediction(ts, order=(1, 1, 0),
                         days=(0, 1, 2, 3, 4, 5, 6)):
    """Plots SARIMA predictions against real values for each weekday.

    :param ts: pandas.core.series.Series
    :param order: tuple
    :param days: tuple
    :return: None
    """
    days_length = len(days)
    if days_length > 2:
        nrows = int(np.ceil(days_length / 2))
        ncols = 2

    else:
        ncols = days_length
        nrows = 1

    fig, ax = plt.subplots(nrows, ncols, squeeze=False)

    if nrows * ncols > days_length:
        fig.delaxes(ax[nrows - 1, ncols - 1])  # one more plot than needed

    fig.suptitle('In-sample Prediction vs Actual')
    weekdays = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday',
                4: 'Friday',
                5: 'Saturday', 6: 'Sunday'}
    title = ts.name

    # fit_list = dview.map_sync(lambda x:
    #                           SARIMAX(
    #                               ts[ts.index.weekday == x],
    #                               order=order,
    #                               seasonal_order=seasonal_order).fit(), days)
    temp_func = functools.partial(ARIMA(endog=None,
                                        order=order).fit())
    fit_list = joblib.Parallel(n_jobs=-1)(joblib.delayed(temp_func)(
            ts_sub=ts[ts.index.weekday == day]) for day in days)

    fit_dict = {day: fit_list[index] for (index, day) in enumerate(days)}

    days_iter = iter(days)
    day = next(days_iter, None)
    for axrow in ax:
        for i in range(ncols):
            if day is not None:
                fit = fit_dict[day]
                axrow[i].set_title(weekdays[day])
                axrow[i].plot(ts.index, ts.values,
                              label='Actual')
                ts_fit = pd.Series(data=fit.predict().flatten(),
                                   index=fit.data.dates)
                ts_fit_filtered = filter_two_std(ts_fit)
                axrow[i].plot(ts_fit_filtered.index, ts_fit_filtered.values,
                              label='Prediction')
                axrow[i].legend(loc='best')
                axrow[i].set_ylabel(title)
                day = next(days_iter, None)
    plt.show()
    plt.draw()
    plt.tight_layout()  # doesn't work without plt.draw coming before
