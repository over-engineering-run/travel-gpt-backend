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

_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root_dir)

from utils import json as js_utils
from init import params as params_init


def _parse_script_arguments() -> dict:

    # parse args
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', type=int, default=0)
    raw_args = parser.parse_args()

    if (raw_args.n is None) or (raw_args.n == 0):
        raise Exception("missing script argument -n")

    args = {
        'n': raw_args.n
    }

    return args


def _init_script_params() -> dict:

    args = _parse_script_arguments()
    envs = params_init.load_environment_variables()

    # app
    if envs['app_host'] is None:
        raise Exception("missing env APP_HOST")
    if envs['app_port'] is None:
        raise Exception("missing env APP_PORT")

    params = {
        'app_host': envs['app_host'],
        'app_port': envs['app_port'],
        'n':        args['n'],
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

    script_logger.info(
        json.dumps(
            script_params,
            indent=4,
        )
    )

    # requests
    success_n, fail_n, skip_n = 0, 0, 0
    for i in range(script_params['n']):

        try:

            # generate random mood message
            gen_resp = requests.post(
                f"http://{script_params['app_host']}:{script_params['app_port']}/v1/mood/generate",
                json={"from_cache": "false"},
                timeout=10
            )

            if (gen_resp.status_code != 200) or \
               (gen_resp.json().get('message') is None) or \
               (len(gen_resp.json().get('message')) == 0):
                raise Exception("failed to generate mood message")

            rand_mood_message = gen_resp.json().get('message')

            if (len(rand_mood_message) > 60) or \
               ('content' in rand_mood_message):
                skip_n += 1
                continue

            # save mood message
            save_resp = requests.post(
                f"http://{script_params['app_host']}:{script_params['app_port']}/v1/mood",
                json={
                    "message":         rand_mood_message,
                    "to_cache":        "true",
                    "mood_message_id": None,
                },
                timeout=3
            )

            if (save_resp.status_code != 200) or \
               (save_resp.json().get('mood_message_id') is None) or \
               (len(save_resp.json().get('mood_message_id')) == 0):
                raise Exception("failed to save mood message")

            new_mood_message_id = save_resp.json().get('mood_message_id')

        except Exception as e:

            fail_n += 1
            script_logger.error(
                "success: %d, failed: %d, skip: %d, current: %d, total: %d, error: %s",
                success_n,
                fail_n,
                skip_n,
                i,
                script_params['n'],
                repr(e),
            )
            time.sleep(1)
            continue

        script_logger.info(
            "success: %d, failed: %d, skip: %d, current: %d, total: %d, info: %s",
            success_n,
            fail_n,
            skip_n,
            i,
            script_params['n'],
            f"new mood message id {new_mood_message_id}"
        )

        # done 1
        success_n += 1

    script_logger.info(
        "success: %d, failed: %d, skip: %d, total: %d, info: %s",
        success_n,
        fail_n,
        skip_n,
        script_params['n'],
        "done cache mood message script"
    )
