"""
Async API Server for for odyssey
"""

import os
import sys

import logging
import json

import uvicorn

from fastapi import FastAPI, Depends, Response

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from sqlalchemy.orm import Session

_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root_dir)

from utils import json as js_utils

from servers.utils import init as server_init
from servers.models.error import ErrorInfo

from databases import database as db_main
from databases.models.mood import MoodMessage as DBMoodMessage


app = FastAPI()
app_params, app_resources, app_logger = server_init.init_server()


@app.get("/healthz")
async def healthz():

    """
    healthz: for endpoint heath checking
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
    trigger_error: endpoint to trigger error for testing
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


@app.get("/v1/mood/{mood_message_id}")
async def get_mood_message(
        mood_message_id: str,
        db: Session = Depends(db_main.get_db_session)
):

    """
    get_mood_message: endpoint to get mood message content by id
    curl -XGET 'http://0.0.0.0:5000/v1/mood/94a1a2d7-0303-47f8-9b1f-2c852413e1e1'
    """

    app_logger.info("endpoint: /v1/mood/<mood_message_id>, info: get request for mood message %s", mood_message_id)

    try:

        # get mood message from db
        db_mood_message = db.query(DBMoodMessage).filter(DBMoodMessage.id == mood_message_id).first()
        if (db_mood_message is None) or (len(db_mood_message.content) == 0):
            raise Exception(f"request mood message {mood_message_id} not found in database")

    except Exception as e:
        req_msg = {'mood_message_id': mood_message_id}
        err_msg = f"endpoint: /v1/mood/<mood_message_id>, error: {repr(e)}, request: {json.dumps(req_msg)}"
        app_logger.error(err_msg)

        err_info = ErrorInfo(
            err_type="FailedToProcessRequest",
            err_msg=err_msg
        )
        return JSONResponse(
            status_code=400,
            content=jsonable_encoder(err_info)
        )

    raw_resp = {
        "mood_message_id": db_mood_message.id,
        "message":         db_mood_message.content
    }
    resp = JSONResponse(
        status_code=200,
        content=jsonable_encoder(raw_resp)
    )

    app_logger.info("endpoint: /v1/mood/<mood_message_id>, info: done request for mood message %s", mood_message_id)

    return resp


if __name__ == '__main__':

    uvicorn.run(
        app=app,
        host=app_params['app_host'],
        port=int(app_params['app_port']),
        log_level=app_logger.level
    )