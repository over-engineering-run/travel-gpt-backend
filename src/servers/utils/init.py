import os
import sys
import multiprocessing
import logging

import argparse
import json

_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root_dir)

from utils import json as js_utils

from init import params as params_init
from init import sentry as init_sentry

from databases import database as db_main
from databases.models.mood import MoodMessage as DBMoodMessage


def _parse_server_arguments() -> dict:

    # parse args
    parser = argparse.ArgumentParser()
    raw_args = parser.parse_args()

    args = {}

    return args


def _init_server_params() -> dict:

    args = _parse_server_arguments()
    envs = params_init.load_environment_variables()

    # app
    if envs['app_host'] is None:
        raise Exception("Missing env APP_HOST")
    if envs['app_port'] is None:
        raise Exception("Missing env APP_PORT")
    if envs['app_auth_token'] is None:
        raise Exception("Missing env APP_AUTH_TOKEN")

    # aws
    if envs['aws_access_id'] is None:
        raise Exception("Missing env AWS_ACCESS_KEY_ID")
    if envs['aws_access_key'] is None:
        raise Exception("Missing env AWS_SECRET_ACCESS_KEY")
    if envs['aws_access_region'] is None:
        raise Exception("Missing env AWS_DEFAULT_REGION")
    if envs['aws_s3_bucket_name'] is None:
        raise Exception("Missing env AWS_S3_BUCKET_NAME")
    if envs['aws_s3_file_path'] is None:
        raise Exception("Missing env AWS_S3_FILE_PATH")

    # db
    if envs['db_dsn'] is None:
        raise Exception("Missing env DB_DSN")

    # google
    if envs['google_api_key'] is None:
        raise Exception("Missing env GOOGLE_API_KEY")

    # openai
    if envs['mood_message_model'] is None:
        raise Exception("Missing env MOOD_MESSAGE_MODEL")
    if envs['mood_image_size'] is None:
        raise Exception("Missing env MOOD_IMAGE_SIZE")

    if envs['openai_api_org'] is None:
        raise Exception("Missing env OPENAI_API_ORG")
    if envs['openai_api_key'] is None:
        raise Exception("Missing env OPENAI_API_KEY")

    # sentry
    if envs['sentry_dsn'] is None:
        raise Exception("Missing env SENTRY_DSN")

    # serpapi
    if envs['serpapi_api_key'] is None:
        raise Exception("Missing env SERPAPI_API_KEY")

    params = {
        'app_host':           envs['app_host'],
        'app_port':           envs['app_port'],
        'app_auth_token':     envs['app_auth_token'],
        'aws_access_id':      envs['aws_access_id'],
        'aws_access_key':     envs['aws_access_key'],
        'aws_access_region':  envs['aws_access_region'],
        'aws_s3_bucket_name': envs['aws_s3_bucket_name'],
        'aws_s3_file_path':   envs['aws_s3_file_path'],
        'db_dsn':             envs['db_dsn'],
        'google_api_key':     envs['google_api_key'],
        'mood_message_model': envs['mood_message_model'],
        'mood_image_size':    envs['mood_image_size'],
        'openai_api_key':     envs['openai_api_key'],
        'openai_api_org':     envs['openai_api_org'],
        'sentry_dsn':         envs['sentry_dsn'],
        'serpapi_api_key':    envs['serpapi_api_key'],
    }

    return params


def _build_server_resources(app_params: dict) -> dict:

    # get number of workers by heuristic
    worker_n = (multiprocessing.cpu_count() * 2) + 1

    # start UvicornWorkers with gunicorn
    server_options = {
        "bind":         f"{app_params['app_host']}:{app_params['app_port']}",
        "workers":      worker_n,
        "worker_class": "uvicorn.workers.UvicornWorker",
        "timeout":      300,
    }

    # start db session
    db = db_main.SessionLocal()

    # mood message
    cached_msg_list = db.query(DBMoodMessage).filter_by(cached=True).all()

    cached_msg_id_list = []
    for msg in cached_msg_list:
        if (msg.content is None) or (len(msg.content.strip()) == 0):
            continue
        cached_msg_id_list.append(str(msg.id))

    # close db session
    db.close()

    # result
    resources = {
        "server_options": server_options,
        'cached_mood_message_id_list': list(set(cached_msg_id_list))
    }

    return resources


def init_server() -> tuple[dict, dict, logging.Logger]:

    # init app params and resources
    app_params    = _init_server_params()
    app_resources = _build_server_resources(app_params=app_params)

    # init logger
    logging.basicConfig(encoding='utf-8', level=logging.INFO)
    app_logger = logging.getLogger("uvicorn.info")

    # init sentry
    init_sentry.init_sentry(dsn=app_params['sentry_dsn'])

    # log debug info
    params_info_str = json.dumps(
        app_params,
        default=js_utils.json_serializer,
        indent=4
    )
    server_options_info_str = json.dumps(
        app_resources['server_options'],
        default=js_utils.json_serializer,
        indent=4
    )
    app_logger.info("app parameters: %s", params_info_str)
    app_logger.info("server options: %s", server_options_info_str)

    return app_params, app_resources, app_logger
