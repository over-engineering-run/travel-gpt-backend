"""
Async API Server for for odyssey
"""

import os
import sys

import logging

import json


import uvicorn

from fastapi import FastAPI

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root_dir)

from servers.dependencies import app_params, app_resources, app_logger

from servers.routers.mood import router as mood_router
from servers.routers.picture import router as picture_router
from servers.routers.spot import router as spot_router

from servers.models.error import ErrorInfo
from servers.models.gunicorn import StandaloneApplication
from servers.utils import init as server_init


app = FastAPI()

app.include_router(mood_router)
app.include_router(picture_router)
app.include_router(spot_router)


@app.get("/healthz")
async def healthz():

    """
    healthz: for heath checking
    curl -XGET 'http://0.0.0.0:5000/healthz'
    """

    resp = JSONResponse(
        status_code=200,
        content={
            "message": "endpoint: /healthz, message: running",
        }
    )

    return resp


@app.get("/error")
async def trigger_error():

    """
    trigger_error: trigger error for testing
    curl -XGET 'http://0.0.0.0:5000/error'
    """

    try:

        _ = 1 / 0

    except Exception as _e:

        err_msg = f"endpoint: /error, error: {repr(_e)}"
        app_logger.error(err_msg)

        err_info = ErrorInfo(
            err_type="FailedToProcessRequest",
            err_msg=err_msg
        )
        resp = JSONResponse(
            status_code=500,
            content=jsonable_encoder(err_info)
        )

        return resp


if __name__ == '__main__':

    StandaloneApplication(
        app,
        app_resources['server_options']
    ).run()
