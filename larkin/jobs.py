# coding=utf-8
import logging
import logging.config
import time

import schedule

import larkin.predictions.run as master_run
from larkin.logging_config import config as log_cfg

logging.config.dictConfig(log_cfg)
logger = logging.getLogger("root")


def sleeping():
    logger.info(
        "All prediction runs are done."
        " I'm going to sleep now, but will wake up again"
        " when it's time to run the scheduled jobs.")


def scheduling():
    logger.info("I've set up the schedule for future runs.")


def waking_up():
    print("\n")
    logger.info("I've woken up.")


def main():
    # for debug
    waking_up()
    scheduling()
    master_run.main()
    sleeping()

    # scheduling
    schedule.every().hour.do(waking_up)
    schedule.every().hour.do(master_run.main)
    schedule.every().hour.do(sleeping)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == 'main':
    main()
