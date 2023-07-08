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

from sqlalchemy import or_, and_, update

_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root_dir)

from utils import json as js_utils

from init import params as params_init

from databases import database as db_main
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

    # get all non-cached s3 picture
    pic_to_found_spot_list = script_db.query(DBPicture) \
                                      .filter(
                                          DBPicture.found_spot == None
                                      ).order_by(
                                          DBPicture.created_at
                                      ).all()

    success_n, fail_n, total_n = 0, 0, len(pic_to_found_spot_list)
    for pic_i, pic_to_found_spot in enumerate(pic_to_found_spot_list):

        try:

            script_logger.info(
                "success: %d, failed: %d, current: %d, total: %d, info: %s",
                success_n,
                fail_n,
                pic_i+1,
                total_n,
                f"finding spot image and spot for picture {pic_to_found_spot.id}"
            )

            # gen mood pic
            pic_resp = requests.get(
                f"http://{script_params['app_host']}:{script_params['app_port']}/v1/spots/search",
                params={"s3_pic_id": pic_to_found_spot.id},
                timeout=60
            )

            # update s3 pic field
            if pic_resp.status_code == 404:

                script_logger.info("spot not found for s3 picture %s", pic_to_found_spot.id)

                result = script_db.execute(
                    update(DBPicture).values(
                        found_spot=False
                    ).where(
                        DBPicture.id == pic_to_found_spot.id
                    )
                )
                script_db.commit()

            elif (pic_resp.json() is not None) and \
                 (pic_resp.json().get('spot_id') is not None):

                script_logger.info(
                    "spot %s found for s3 picture %s",
                    pic_resp.json().get('spot_id'),
                    pic_to_found_spot.id
                )

                result = script_db.execute(
                    update(DBPicture).values(
                        found_spot=True
                    ).where(
                        DBPicture.id == pic_to_found_spot.id
                    )
                )
                script_db.commit()

            else:
                raise Exception("unknown error")
                continue

            success_n += 1

        except Exception as e:

            fail_n += 1
            script_logger.error(
                "success: %d, failed: %d, current: %d, total: %d, error: %s",
                success_n,
                fail_n,
                pic_i+1,
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
        "done cache spot script"
    )
