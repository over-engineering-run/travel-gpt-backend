"""
Async API Server for for odyssey
"""

import os
import sys

import argparse

import logging
import json

import time
import requests

from sqlalchemy import or_, and_

_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root_dir)

from utils import json as js_utils

from init import params as params_init

from databases import database as db_main
from databases.models.mood import MoodMessage as DBMoodMessage
from databases.models.mood import MoodPicture as DBMoodPicture
from databases.models.picture import Picture as DBPicture


def _parse_script_arguments() -> dict:

    # parse args
    parser = argparse.ArgumentParser()
    raw_args = parser.parse_args()

    args = {}

    return args


def _init_script_params() -> dict:

    args = _parse_script_arguments()
    envs = params_init.load_environment_variables()

    # app
    if envs['app_host'] is None:
        raise Exception("missing env APP_HOST")
    if envs['app_port'] is None:
        raise Exception("missing env APP_PORT")

    # db
    if envs['db_dsn'] is None:
        raise Exception("Missing env DB_DSN")

    params = {
        'app_host': envs['app_host'],
        'app_port': envs['app_port'],
        'db_dsn': envs['db_dsn'],
    }

    return params


def _init_logging() -> logging.Logger:

    logging.basicConfig(encoding='utf-8', level=logging.INFO)
    logger = logging.getLogger(__name__)

    return logger


if __name__ == '__main__':

    # init
    script_logger = _init_logging()
    script_params = _init_script_params()
    script_db = db_main.SessionLocal()

    script_logger.info(
        json.dumps(
            script_params,
            indent=4,
        )
    )

    # get all cached mood messages
    cached_msg_list = script_db.query(DBMoodMessage.id) \
                               .join(
                                   DBMoodPicture,
                                   DBMoodMessage.id == DBMoodPicture.mood_message_id,
                                   isouter=True
                               ).join(
                                   DBPicture,
                                   DBMoodPicture.id == DBPicture.reference_id,
                                   isouter=True
                               ).filter(
                                   DBMoodMessage.cached == True
                               ).filter(
                                   or_(
                                       DBMoodPicture.id == None,
                                       DBPicture.id == None
                                   )
                               ).all()

    success_n, fail_n, total_n = 0, 0, len(cached_msg_list)
    for msg_i, cached_msg in enumerate(cached_msg_list):

        try:

            script_logger.info(
                "success: %d, failed: %d, current: %d, total: %d, info: %s",
                success_n,
                fail_n,
                msg_i+1,
                total_n,
                f"generating mood picture for mood message {cached_msg.id}"
            )

            # gen mood pic
            pic_resp = requests.post(
                f"http://{script_params['app_host']}:{script_params['app_port']}/v1/mood/{cached_msg.id}/picture",
                json={"used_mood_pic_ids": []},
                timeout=10
            )
            mood_pic_id = pic_resp.json().get('mood_pic_id')

            # save mood pic to s3
            pic_resp = requests.post(
                f"http://{script_params['app_host']}:{script_params['app_port']}/v1/pictures",
                json={"type": "mood_pic", "id": mood_pic_id},
                timeout=10
            )

            success_n += 1

        except Exception as e:

            fail_n += 1
            script_logger.error(
                "success: %d, failed: %d, current: %d, total: %d, error: %s",
                success_n,
                fail_n,
                msg_i+1,
                total_n,
                repr(e),
            )
            time.sleep(1)
            continue

    script_logger.info(
        "success: %d, failed: %d, total: %d, info: %s",
        success_n,
        fail_n,
        total_n,
        "done cache mood picture script"
    )
