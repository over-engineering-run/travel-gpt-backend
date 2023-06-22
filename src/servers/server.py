"""
Async API Server for for odyssey
"""

import os
import sys

import logging
import json

import uvicorn

from fastapi import FastAPI, Response

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root_dir)

from utils import json as js_utils

from servers.utils import init as server_init
from databases.database import get_db_session


app = FastAPI()
app_params, app_resources, app_logger = server_init.init_server(__name__)


@app.get("/healthz")
async def healthz():

    """
    healthz: for endpoint heath checking
    curl -XGET 'http://0.0.0.0:5000/healthz'
    """

    resp = JSONResponse(
        status_code=200,
        content={
            "message":       "endpoint: /healthz, message: running",
            "error_type":    None,
            "error_message": None
        }
    )

    return resp


@app.get("/error")
async def trigger_error():

    """
    trigger_error: endpoint to trigger error for testing
    curl -XGET 'http://0.0.0.0:5000/error'
    """

    try:

        _ = 1 / 0

    except Exception as _e:

        err_msg = f"endpoint: /error, error: {repr(_e)}"
        app_logger.error(err_msg)

        resp = JSONResponse(
            status_code=500,
            content={
                "error_type":    "ZeroDivisionError",
                "error_message": err_msg
            }
        )

        return resp


if __name__ == '__main__':

    uvicorn.run(
        app=app,
        host=app_params['app_host'],
        port=int(app_params['app_port']),
        log_level=logging.INFO
    )
