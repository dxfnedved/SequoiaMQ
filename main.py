# -*- encoding: UTF-8 -*-

import utils
import logging
import work_flow
import settings
import schedule
import time
import datetime
from pathlib import Path


def job():
    if utils.is_weekday():
        work_flow.prepare()


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='sequoia.log',
    filemode='a'
)

logging.getLogger('RARA_Strategy').setLevel(logging.DEBUG)

settings.init()

if settings.config['cron']:
    EXEC_TIME = "15:15"
    schedule.every().day.at(EXEC_TIME).do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)
else:
    work_flow.prepare()

logger = logging.getLogger('Alpha_Strategy')
logger.setLevel(logging.INFO)
fh = logging.FileHandler('alpha_strategy.log')
fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(fh)
