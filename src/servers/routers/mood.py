import os
import sys

import json
from typing import Optional

import random

from fastapi import APIRouter, Depends, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from sqlalchemy.orm import Session
from sqlalchemy import desc

_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root_dir)

from servers.dependencies import app_params, app_resources, app_logger

from servers.utils import model as model_utils

from servers.models.error import ErrorInfo
from servers.models import mood as mood_models

from servers.logics import mood as mood_logics

from databases import database as db_main
from databases.models.mood import MoodMessage as DBMoodMessage
from databases.models.mood import MoodPicture as DBMoodPicture
from databases.models.picture import Picture as DBPicture


router = APIRouter(
    prefix="/v1/mood"
)


@router.get("/{mood_message_id}")
async def get_mood_message(
        mood_message_id: str,
        db: Session = Depends(db_main.get_db_session)
):

    """
    get_mood_message: get mood message content by id
    curl -XGET 'http://0.0.0.0:5000/v1/mood/dece78f8-5fce-42c3-8fb3-ed1cc2929e63'
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


@router.post("/generate")
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
                    app_logger.info(f"return cached mood message {cached_msg_id} from database")

        # generate by openai
        if (random_mood_str is None) or (len(random_mood_str.strip()) == 0):

            # TODO: resolve worker timeout
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


@router.post("/")
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


@router.post("/{mood_message_id}/picture")
async def post_mood_message_to_mood_picture(
        req_body: dict,
        mood_message_id: str,
        db: Session = Depends(db_main.get_db_session)
):

    """
    post_mood_message_to_mood_picture: get mood picture from mood message
    curl -XPOST 'http://0.0.0.0:5000/v1/mood/4498fca1-ad59-4dfa-b625-c58a454e1138/picture' -H 'Content-Type: application/json' -d '{"used_mood_pic_ids": []}'
    """

    app_logger.info(
        "endpoint: /v1/mood/<mood_message_id>/picture, info: get request for generating picture from mood message %s",
        mood_message_id
    )

    err_status_code = 500
    err_type = "FailedToProcessRequest"
    try:

        # check request body
        if (req_body is None) or (len(req_body) == 0):
            err_status_code = 400
            err_type = "InvalidRequest"
            raise Exception("request body is empty")

        # parse used mood picture ids
        used_mood_pic_ids = req_body.get('used_mood_pic_ids')
        if (used_mood_pic_ids is None):
            err_status_code = 400
            err_type = "InvalidRequest"
            raise Exception("request body missing used_mood_pic_ids")
        used_mood_pic_id_set = set(used_mood_pic_ids)

        # check mood_message_id
        if (mood_message_id is None) or (len(mood_message_id) == 0):
            err_status_code = 400
            err_type = "InvalidRequest"
            raise Exception("failed to parse mood_message_id")

        # get mood message from db
        db_mood_msg = db.get(DBMoodMessage, mood_message_id)
        if (db_mood_msg is None) or (len(db_mood_msg.content) == 0):
            err_status_code = 404
            err_type = "InvalidRequest"
            raise Exception(f"mood message {mood_message_id} not found in database")

        # try to get from cache
        db_s3_pic_list = db.query(DBPicture) \
                           .join(
                               DBMoodPicture,
                               DBMoodPicture.id == DBPicture.reference_id,
                               isouter=True
                           ).filter(
                               DBPicture.reference_type == "mood_pic"
                           ).filter(
                               DBMoodPicture.mood_message_id == db_mood_msg.id
                           ).order_by(
                               desc(DBMoodPicture.created_at)
                           ).all()

        if (db_s3_pic_list is not None) and (len(db_s3_pic_list) > 0):

            for db_s3_pic in db_s3_pic_list:

                if str(db_s3_pic.reference_id) not in used_mood_pic_id_set:

                    raw_resp = {
                        "mood_pic_id":   db_s3_pic.reference_id,
                        "mood_pic_url":  db_s3_pic.url,
                        "mood_pic_size": db_s3_pic.size
                    }
                    resp = JSONResponse(
                        status_code=200,
                        content=jsonable_encoder(raw_resp)
                    )

                    app_logger.info(
                        "endpoint: /v1/mood/<mood_message_id>/picture, info: found cached mood picture %s for mood message %s",
                        db_s3_pic.reference_id,
                        mood_message_id
                    )

                    return resp

        # TODO: resolve worker timeout
        # if not cached mood picture not found, generate by openai
        svr_mood_msg = model_utils.db_mood_message_to_server_mood_message(db_mood_msg)
        image_size   = app_params['mood_image_size']
        svr_mood_pic = mood_logics.generate_mood_image_by_description(
            mood_msg=svr_mood_msg,
            image_size=image_size,
        )

        # save generated mood picture
        db_mood_pic = DBMoodPicture(
            uuid_str=svr_mood_pic.uuid,
            url=svr_mood_pic.url,
            size=svr_mood_pic.size,
            prompt=svr_mood_pic.prompt,
            model=svr_mood_pic.model,
            mood_message_id=mood_message_id
        )
        db.add(db_mood_pic)
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
        "mood_pic_id":   db_mood_pic.id,
        "mood_pic_url":  db_mood_pic.url,
        "mood_pic_size": db_mood_pic.size
    }
    resp = JSONResponse(
        status_code=200,
        content=jsonable_encoder(raw_resp)
    )

    app_logger.info(
        "endpoint: /v1/mood/<mood_message_id>/picture, info: done generating picture %s from mood message %s",
        db_mood_pic.id,
        mood_message_id
    )

    return resp
