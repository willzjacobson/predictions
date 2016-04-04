import random
import pickle

import pandas as pd

from larkin.predictions.startup.run import main

__author__ = 'davidkarapetyan'

past_starts = pd.read_excel("/home/davidkarapetyan/Documents/workspace/data/"
                            "csvs_xlsx/startup_park345.xlsx", sheetname=None,
                            )

master = pd.concat(past_starts.values())
master = master[["Date", "Start Time ", "End Time"]]
master = master.rename(columns={
    "Date": "date",
    "Start Time ": "start_time",
    "End Time": "end_time"
})
master = master.dropna()
master = master.reset_index(drop=True)
# master = master.set_index('date')
# master = master.sort_index()
master = master[master.start_time.str.contains('.*[0-9].*')]

start_times = pd.Series(index=pd.to_datetime(master.date.apply(str) + " " +
                                             master.start_time))
start_times = start_times.tz_localize('America/New_York').tz_convert('utc')
start_times = start_times.sort_index()

##### compare fits to actual rudin

rudin_dates = pd.date_range(
    start='2015-08-01 00:00:00+00:00', end=start_times.index[-1], freq='1H',
    tz='utc')
early = rudin_dates[rudin_dates.hour == 4]
ran_samp = pd.Series(index=random.sample(early, k=100)).index
rudin_fits = []
for date in ran_samp:
    rudin_fits.extend(main(date, debug=True, buildings=["345_Park"])[
                          "345_Park"]["random_forest"]["best_start_time"])

pickle.dump(rudin_fits,
            "/home/davidkarapetyan/Documents/workspace/data/100_runs_rudin")


################ Columbia
# tpo_dates = pd.date_range(
#     start="2013-05-07", end="2014-11-15", freq='1H', tz='utc')
# early = tpo_dates[tpo_dates.hour == 4]
# ran_samp = pd.Series(index=random.sample(early, k=100)).index
# tpo_fits = []
# for date in ran_samp:
#     tpo_fits.extend(main(date))
#
# pickle.dump(tpo_fits,
#             "/home/davidkarapetyan/Documents/workspace/data/100_runs_tpo")
