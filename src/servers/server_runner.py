import os
import sys

import logging
import argparse

from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from waitress import serve

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

from init import params as params_init
from init import db as db_init

from databases import databases
from servers.servers import api_server


def create_app():

    """Application-factory pattern"""

    app = Flask(__name__)

    Limiter(
        get_remote_address,
        app=app,
        default_limits=["3 per second"],
        storage_uri="memory://",
    )

    CORS(
        app,
        resources={
            r"/v1/*": {"origins": "*"},
        }
    )

    return app


def _parse_server_arguments():

    # parse args
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', type=bool, default=False)
    raw_args = parser.parse_args()

    args = {
        'app_debug': raw_args.debug,
    }

    return args


def _init_server_params():

    args = _parse_server_arguments()
    envs = params_init.load_environment_variables()

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
    if envs['openai_api_org'] is None:
        raise Exception("Missing env OPENAI_API_ORG")
    if envs['openai_api_key'] is None:
        raise Exception("Missing env OPENAI_API_KEY")

    if envs['mood_message_model'] is None:
        raise Exception("Missing env MOOD_MESSAGE_MODEL")
    if envs['mood_image_size'] is None:
        raise Exception("Missing env MOOD_IMAGE_SIZE")

    # serpapi
    if envs['serpapi_api_key'] is None:
        raise Exception("Missing env SERPAPI_API_KEY")

    params = {
        'app_debug':          args['app_debug'] or envs['app_debug'],
        'app_host':           envs['app_host'],
        'app_name':           envs['app_name'],
        'app_port':           envs['app_port'],
        'db_dsn':             envs['db_dsn'],
        'openai_api_key':     envs['openai_api_key'],
        'openai_api_org':     envs['openai_api_org'],
        'mood_message_model': envs['mood_message_model'],
        'mood_image_size':    envs['mood_image_size'],
        'aws_access_id':      envs['aws_access_id'],
        'aws_access_key':     envs['aws_access_key'],
        'aws_access_region':  envs['aws_access_region'],
        'aws_s3_bucket_name': envs['aws_s3_bucket_name'],
        'aws_s3_file_path':   envs['aws_s3_file_path'],
        'google_api_key':     envs['google_api_key'],
        'openai_api_key':     envs['openai_api_key'],
        'openai_api_org':     envs['openai_api_org'],
        'serpapi_api_key':    envs['serpapi_api_key'],
    }

    return params


if __name__ == '__main__':

    app = create_app()
    params = _init_server_params()
    db, db_migrate = db_init.init_db(databases.db, databases.migrate, app, params)

    # server
    if params['app_debug']:  # debug

        logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

        server = api_server.APIServer(app, params, db)
        server.run()

    else:  # production

        logging.basicConfig(encoding='utf-8', level=logging.INFO)

        server = api_server.APIServer(app, params, db)
        serve(
            server.app,
            host=params['app_host'],
            port=params['app_port'],
        )
