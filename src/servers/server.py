"""
Async API Server for for odyssey
"""

import os
import sys

import logging
from typing import Optional

import json
import random

import uvicorn

from fastapi import FastAPI, Depends, Response

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from sqlalchemy import desc
from sqlalchemy.orm import Session

_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root_dir)

from utils import json as js_utils

from servers.models.error import ErrorInfo
from servers.models import mood as mood_models

from servers.utils import init as server_init
from servers.utils import model as model_utils

from servers.logics import mood as mood_logics
from servers.logics import picture as pic_logics
from servers.logics import spot as spot_logics

from databases import database as db_main
from databases.models.mood import MoodMessage as DBMoodMessage
from databases.models.mood import MoodPicture as DBMoodPicture
from databases.models.picture import Picture as DBPicture
from databases.models.spot import SpotImage as DBSpotImage
from databases.models.spot import Spot as DBSpot


app = FastAPI()
app_params, app_resources, app_logger = server_init.init_server()


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


@app.get("/v1/mood/{mood_message_id}")
async def get_mood_message(
        mood_message_id: str,
        db: Session = Depends(db_main.get_db_session)
):

    """
    get_mood_message: get mood message content by id
    curl -XGET 'http://0.0.0.0:5000/v1/mood/94a1a2d7-0303-47f8-9b1f-2c852413e1e1'
    """

    app_logger.info(
        "endpoint: /v1/mood/<mood_message_id>, info: get request for mood message %s",
        mood_message_id
    )

    err_status_code = 500
    err_type = "FailedToProcessRequest"
    try:

        # check mood_message_id
        if (mood_message_id is None) or (len(mood_message_id.strip()) == 0):
            err_status_code = 400
            err_type = "InvalidRequest"
            raise Exception("missing mood_message_id")

        # get mood message from db
        db_mood_message = db.get(DBMoodMessage, mood_message_id)
        if (db_mood_message is None) or (len(db_mood_message.content) == 0):
            err_status_code = 404
            err_type = "InvalidRequest"
            raise Exception(f"mood message {mood_message_id} not found in database")

    except Exception as e:
        req_msg = {'mood_message_id': mood_message_id}
        err_msg = f"endpoint: /v1/mood/<mood_message_id>, error: {repr(e)}, request: {json.dumps(req_msg)}"
        app_logger.error(err_msg)

        err_info = ErrorInfo(
            err_type=err_type,
            err_msg=err_msg
        )
        return JSONResponse(
            status_code=err_status_code,
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

    app_logger.info(
        "endpoint: /v1/mood/<mood_message_id>, info: done request for mood message %s",
        mood_message_id
    )

    return resp


@app.post("/v1/mood/generate")
async def generate_mood_message(
        req_body: Optional[dict] = None,
        db: Session = Depends(db_main.get_db_session)
):

    """
    generate_mood_message: generate random mood message
    curl -XPOST 'http://0.0.0.0:5000/v1/mood/generate' -H 'Content-Type: application/json' -d '{"from_cache": "false"}'
    """

    app_logger.info(
        "endpoint: /v1/mood/generate, info: get request for generating random mood message"
    )

    err_status_code = 500
    err_type = "FailedToProcessRequest"
    try:

        # from cache or not
        if req_body is not None:
            req_cache_bool_str = req_body.get('from_cache', 'true')
            req_cache_bool = req_cache_bool_str.lower() != 'false'
        else:
            req_cache_bool = True

        # get or generate mood message
        random_mood_str = ""
        random_mood_id  = None

        # try to get from cached
        if req_cache_bool:

            cached_mood_message_id_list = app_resources['cached_mood_message_id_list']
            cached_msg_n = len(cached_mood_message_id_list)

            if cached_msg_n > 0:

                cached_i = random.randint(0, cached_msg_n-1)
                cached_msg_id = cached_mood_message_id_list[cached_i]

                db_mood_msg = db.get(DBMoodMessage, cached_msg_id)
                if (db_mood_msg is None) or (len(db_mood_msg.content) == 0):
                    app_logger.error(f"cached mood message {cached_msg_id} not found in database")
                else:
                    random_mood_id  = db_mood_msg.id
                    random_mood_str = db_mood_msg.content
                    app_logger.info(f"return random cached mood message {cached_msg_id} from database")

        # generate by openai
        if (random_mood_str is None) or (len(random_mood_str.strip()) == 0):
            random_mood_str = mood_logics.generate_random_mood_message(
                model=app_params['mood_message_model']
            )

    except Exception as e:
        err_msg = f"endpoint: /v1/mood/generate, error: {repr(e)}"
        app_logger.error(err_msg)

        err_info = ErrorInfo(
            err_type=err_type,
            err_msg=err_msg
        )
        return JSONResponse(
            status_code=err_status_code,
            content=jsonable_encoder(err_info)
        )

    raw_resp = {
        "req_cache_bool":  req_cache_bool,
        "mood_message_id": random_mood_id,
        "message":         random_mood_str
    }
    resp = JSONResponse(
        status_code=200,
        content=jsonable_encoder(raw_resp)
    )

    app_logger.info(
        "endpoint: /v1/mood/generate, info: done request for generating random mood message %s",
        random_mood_id
    )

    return resp


@app.post("/v1/mood")
async def post_mood_message(
        req_body: dict,
        db: Session = Depends(db_main.get_db_session)
):

    """
    post_mood_message: save mood message to db
    curl -XPOST 'http://0.0.0.0:5000/v1/mood' -H 'Content-Type: application/json' -d '{"to_cache": "true", "message": "I am happy", "mood_message_id": null}'
    """

    app_logger.info("endpoint: /v1/mood, info: get request for saving mood message to db")

    err_status_code = 500
    err_type = "FailedToProcessRequest"
    try:

        # check request body
        if (req_body is None) or (len(req_body) == 0):
            err_status_code = 400
            err_type = "InvalidRequest"
            raise Exception("request body is empty")

        # parse mood message content
        req_mood_msg_content = req_body.get('message')
        if (req_mood_msg_content is None) or (len(req_mood_msg_content.strip()) == 0):
            err_status_code = 400
            err_type = "InvalidRequest"
            raise Exception("request body missing mood message")

        # check if there is mood message id for later cached checking
        req_mood_msg_id = req_body.get('mood_message_id')
        if (req_mood_msg_id is not None) and (len(req_mood_msg_id) > 0):

            # check for cache
            db_mood_msg = db.get(DBMoodMessage, req_mood_msg_id)

            if (db_mood_msg is not None) \
               and (db_mood_msg.cached is True) \
               and (db_mood_msg.content.strip() == req_mood_msg_content.strip()):

                raw_resp = {
                    "mood_message_id": db_mood_msg.id
                }
                resp = JSONResponse(
                    status_code=200,
                    content=jsonable_encoder(raw_resp)
                )

                app_logger.info(
                    "endpoint: /v1/mood, info: found cached mood message %s in db",
                    db_mood_msg.id
                )

                return resp

        # if not cached create a new mood message
        req_cache_bool_str = req_body.get('to_cache', 'false')
        req_cache_bool = req_cache_bool_str.lower() == 'true'

        mood_msg = mood_models.MoodMessage(
            content=req_mood_msg_content,
            cached=req_cache_bool
        )

        # save to db
        db_mood_msg = DBMoodMessage(
                uuid_str=mood_msg.uuid,
                content=mood_msg.content,
                prompt=mood_msg.prompt,
                model=app_params['mood_message_model'],
                cached=mood_msg.cached
            )
        db.add(db_mood_msg)
        db.commit()

    except Exception as e:
        err_msg = f"endpoint: /v1/mood, error: {repr(e)}"
        app_logger.error(err_msg)

        err_info = ErrorInfo(
            err_type=err_type,
            err_msg=err_msg
        )
        return JSONResponse(
            status_code=err_status_code,
            content=jsonable_encoder(err_info)
        )

    raw_resp = {
        "mood_message_id": db_mood_msg.id
    }
    resp = JSONResponse(
        status_code=200,
        content=jsonable_encoder(raw_resp)
    )

    app_logger.info(
        "endpoint: /v1/mood, info: done request for saving mood message %s to db",
        db_mood_msg.id
    )

    return resp


@app.get("/v1/pictures/{s3_pic_id}")
async def get_picture(
        s3_pic_id: str,
        db: Session = Depends(db_main.get_db_session)
):

    """
    get_picture: get s3 picture info from by id
    curl -XGET 'http://0.0.0.0:5000/v1/pictures/3496ba34-4022-4109-9e3c-6aae37d658a1'
    """

    app_logger.info("endpoint: /v1/pictures/<s3_pic_id>, info: get request for s3 picture %s", s3_pic_id)

    err_status_code = 500
    err_type = "FailedToProcessRequest"
    try:

        # check s3_pic_id
        if (s3_pic_id is None) or (len(s3_pic_id.strip()) == 0):
            err_status_code = 400
            err_type = "InvalidRequest"
            raise Exception("missing s3_pic_id")

        # get mood message from db
        db_picture = db.get(DBPicture, s3_pic_id)
        if (db_picture is None) or (len(db_picture.url) == 0):
            err_status_code = 404
            err_type = "InvalidRequest"
            raise Exception(f"mood message {s3_pic_id} not found in database")

    except Exception as e:
        req_msg = {'s3_pic_id': s3_pic_id}
        err_msg = f"endpoint: /v1/pictures/<s3_pic_id>, error: {repr(e)}, request: {json.dumps(req_msg)}"
        app_logger.error(err_msg)

        err_info = ErrorInfo(
            err_type=err_type,
            err_msg=err_msg
        )
        return JSONResponse(
            status_code=err_status_code,
            content=jsonable_encoder(err_info)
        )

    raw_resp = {
        "s3_pic_id":   db_picture.id,
        "s3_pic_url":  db_picture.url,
        "s3_pic_size": db_picture.size
    }
    resp = JSONResponse(
        status_code=200,
        content=jsonable_encoder(raw_resp)
    )

    app_logger.info("endpoint: /v1/pictures/<s3_pic_id>, info: done request for s3 picture %s", s3_pic_id)

    return resp


@app.post("/v1/pictures")
async def post_picture(
        req_body: dict,
        db: Session = Depends(db_main.get_db_session)
):

    """
    post_picture: save picture to s3
    curl -XPOST 'http://0.0.0.0:5000/v1/pictures' -H 'Content-Type: application/json' -d '{"type": "mood_pic", "id": "0d2622f2-f484-487a-a647-6b5ef2da1252"}'
    """

    err_status_code = 500
    err_type = "FailedToProcessRequest"
    try:

        # check request body
        if (req_body is None) or (len(req_body) == 0):
            err_status_code = 400
            err_type = "InvalidRequest"
            raise Exception("request body is empty")

        # parse picture reference type
        pic_ref_type = req_body.get('type')
        if (pic_ref_type is None) or (len(pic_ref_type) == 0):
            err_status_code = 400
            err_type = "InvalidRequest"
            raise Exception("request body missing type")

        # parse picture reference id
        pic_ref_id = req_body.get('id')
        if (pic_ref_id is None) or (len(pic_ref_id) == 0):
            err_status_code = 400
            err_type = "InvalidRequest"
            raise Exception("request body missing id")

        app_logger.info("endpoint: /v1/pictures, info: get request for saving %s id %s to s3", pic_ref_type, pic_ref_id)

        # get mood picture by mood id from db
        if pic_ref_type == 'mood_pic':

            # check if pic already save on s3
            db_pic = db.query(DBPicture) \
                       .filter(DBPicture.reference_id == pic_ref_id) \
                       .order_by(desc(DBPicture.created_at)) \
                       .first()

            if db_pic is not None:

                app_logger.info("mood picture %s found already on s3", pic_ref_id)

            else:

                # get mood picture from db
                db_mood_pic = db.get(DBMoodPicture, pic_ref_id)
                if (db_mood_pic is None) or (len(db_mood_pic.url) == 0):
                    err_status_code = 404
                    err_type = "InvalidRequest"
                    raise Exception(f"mood picture {db_mood_pic} not found in database")

                # db to svr mood picture
                svr_mood_pic = model_utils.db_mood_picture_to_server_mood_picture(db_mood_pic)

                # save pic to s3
                svr_picture = pic_logics.save_picture_to_s3_by_url(
                    source_url=svr_mood_pic.url,
                    source_size=svr_mood_pic.size,
                    s3_region=app_params['aws_access_region'],
                    s3_bucket_name=app_params['aws_s3_bucket_name'],
                    s3_file_path=app_params['aws_s3_file_path']
                )

                # save pic to db
                db_pic = DBPicture(
                    uuid_str=svr_picture.uuid,
                    filename=svr_picture.filename,
                    size=svr_picture.size,
                    url=svr_picture.url,
                    reference_type=pic_ref_type,
                    reference_id=pic_ref_id,
                )
                db.add(db_pic)
                db.commit()

    except Exception as e:
        err_msg = f"endpoint: /v1/pictures, error: {repr(e)}, request: {json.dumps(req_body)}"
        app_logger.error(err_msg)

        err_info = ErrorInfo(
            err_type=err_type,
            err_msg=err_msg
        )
        return JSONResponse(
            status_code=err_status_code,
            content=jsonable_encoder(err_info)
        )

    raw_resp = {
        "s3_pic_id":   db_pic.id,
        "s3_pic_url":  db_pic.url,
        "s3_pic_size": db_pic.size
    }
    resp = JSONResponse(
        status_code=200,
        content=jsonable_encoder(raw_resp)
    )

    app_logger.info("endpoint: /v1/pictures, info: done request for saving %s id %s to s3", pic_ref_type, pic_ref_id)

    return resp


if __name__ == '__main__':

    uvicorn.run(
        app=app,
        host=app_params['app_host'],
        port=int(app_params['app_port']),
        log_level=app_logger.level
    )
