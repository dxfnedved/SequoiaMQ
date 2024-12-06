# -*- encoding: UTF-8 -*-

import utils
import logging
import work_flow
import settings
import schedule
import time
import datetime
from pathlib import Path
import sys
import stock_selector

def job():
    if utils.is_weekday():
        work_flow.prepare()

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='sequoia.log',
        filemode='a'
    )

    logging.getLogger('RARA_Strategy').setLevel(logging.DEBUG)
    
    logger = logging.getLogger('Alpha_Strategy')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler('alpha_strategy.log')
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)

def main():
    setup_logging()
    settings.init()
    
    # 检查是否有命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == '--gui':
        # GUI模式
        stock_selector.main()
    else:
        # 传统模式
        if settings.config['cron']:
            EXEC_TIME = "15:15"
            schedule.every().day.at(EXEC_TIME).do(job)

            while True:
                schedule.run_pending()
                time.sleep(1)
        else:
            work_flow.prepare()

if __name__ == "__main__":
    main()
