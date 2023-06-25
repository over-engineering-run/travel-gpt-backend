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
                    app_logger.info(f"return cached mood message {cached_msg_id} from database")

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


@app.post("/v1/mood/{mood_message_id}/picture")
async def post_mood_message_to_mood_picture(
        req_body: dict,
        mood_message_id: str,
        db: Session = Depends(db_main.get_db_session)
):

    """
    post_mood_message_to_mood_picture: get mood picture from mood message
    curl -XPOST 'http://0.0.0.0:5000/v1/mood/98d1cc6c-421f-4aa5-9268-769ac5c45c33/picture' -H 'Content-Type: application/json' -d '{"used_mood_pic_ids": ["436da2de-1c06-4968-9844-47cb46aa95ba"]}'
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
        db_mood_pic_list = db.query(DBMoodPicture) \
                             .filter(DBMoodPicture.mood_message_id == db_mood_msg.id) \
                             .order_by(desc(DBMoodPicture.created_at)) \
                             .all()

        if (db_mood_pic_list is not None) and (len(db_mood_pic_list) > 0):

            for db_mood_pic in db_mood_pic_list:

                if str(db_mood_pic.id) not in used_mood_pic_id_set:

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
                        "endpoint: /v1/mood/<mood_message_id>/picture, info: found cached mood picture %s for mood message %s",
                        db_mood_pic.id,
                        mood_message_id
                    )

                    return resp

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


@app.get("/v1/pictures/{s3_pic_id}")
async def get_picture(
        s3_pic_id: str,
        db: Session = Depends(db_main.get_db_session)
):

    """
    get_picture: get s3 picture info from by id
    curl -XGET 'http://0.0.0.0:5000/v1/pictures/3496ba34-4022-4109-9e3c-6aae37d658a1'
    """

    app_logger.info(
        "endpoint: /v1/pictures/<s3_pic_id>, info: get request for s3 picture %s",
        s3_pic_id
    )

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
            raise Exception(f"s3 picture {s3_pic_id} not found in database")

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

    app_logger.info(
        "endpoint: /v1/pictures/<s3_pic_id>, info: done request for s3 picture %s",
        s3_pic_id
    )

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

        app_logger.info(
            "endpoint: /v1/pictures, info: get request for saving %s id %s to s3",
            pic_ref_type,
            pic_ref_id
        )

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

    app_logger.info(
        "endpoint: /v1/pictures, info: done request for saving %s id %s to s3",
        pic_ref_type,
        pic_ref_id
    )

    return resp


@app.get("/v1/spots/search")
async def get_spot_search_by_picture(
        s3_pic_id: str,
        db: Session = Depends(db_main.get_db_session)
):

    """
    post_mood_message_to_mood_picture: get mood picture from mood message
    curl -XGET 'http://0.0.0.0:5000/v1/spots/search?s3_pic_id=7ddfad56-24b8-4929-9af5-68a681593f41'
    """

    app_logger.info(
        "endpoint: /v1/spots/search, info: get request for searching spot with picture %s",
        s3_pic_id
    )

    err_status_code = 500
    err_type = "FailedToProcessRequest"
    try:

        # check s3_pic_id
        if (s3_pic_id is None) or (len(s3_pic_id) == 0):
            err_status_code = 400
            err_type = "InvalidRequest"
            raise Exception("failed to parse s3_pic_id")

        # get s3 picture from db
        db_picture = db.get(DBPicture, s3_pic_id)
        if (db_picture is None) or (len(db_picture.url) == 0):
            err_status_code = 404
            err_type = "InvalidRequest"
            raise Exception(f"s3 picture {s3_pic_id} not found in database")

        # try to get from cache
        db_spot_img_list = db.query(DBSpotImage) \
                             .filter(DBSpotImage.reference_id == db_picture.id) \
                             .order_by(desc(DBSpotImage.created_at)) \
                             .all()

        if (db_spot_img_list is not None) and (len(db_spot_img_list) > 0):

            for db_spot_img in db_spot_img_list:

                db_spot = db.query(DBSpot) \
                            .filter(DBSpot.spot_image_id == db_spot_img.id) \
                            .order_by(desc(DBSpot.created_at)) \
                            .first()

                if db_spot is not None:

                    raw_resp = {
                        "spot_id":    db_spot.id,
                        "created_at": db_spot.created_at,
                        "address":    db_spot.address,
                        "name":       db_spot.name,
                        "rating":     db_spot.rating,
                        "rating_n":   db_spot.rating_n,
                        "place_id":   db_spot.place_id,
                        "reference":  db_spot.reference,
                        "types":      db_spot.types,
                        "geometry":   db_spot.geometry,
                        "image": {
                            "id":  db_spot_img.id,
                            "url": db_spot_img.thumbnail
                        }
                    }

                    resp = JSONResponse(
                        status_code=200,
                        content=jsonable_encoder(raw_resp)
                    )

                    app_logger.info(
                        "endpoint: /v1/spots/search, info: found cached spot %s for picture %s",
                        db_spot.id,
                        s3_pic_id
                    )

                    return resp

        # search: s3 picture (mood image) -> spot image
        spot_img_list = spot_logics.search_spot_image_by_pic_url(
            api_key=app_params['serpapi_api_key'],
            pic_url=db_picture.url
        )
        app_logger.info("found %d spot image for s3 picture %s", len(spot_img_list), s3_pic_id)

        # spot image -> spot
        spot_result = None
        for spot_img in spot_img_list:

            if spot_img is None:
                continue

            spot_list = spot_logics.search_spot_by_spot_image(
                api_key=app_params['google_api_key'],
                image=spot_img,
            )

            if len(spot_list) > 0:
                spot_result = spot_list[0]
                spot_result.image = spot_img
                break

        # update spot image and spot to db
        if spot_result is None:

            raw_resp = {
                "spot_id":    None,
                "created_at": None,
                "address":    None,
                "name":       None,
                "rating":     None,
                "rating_n":   None,
                "place_id":   None,
                "reference":  None,
                "types":      None,
                "geometry":   None,
                "image": {
                    "id":  None,
                    "url": None
                }
            }
            resp = JSONResponse(
                status_code=200,
                content=jsonable_encoder(raw_resp)
            )

            return resp

        else:

            db_spot_img = DBSpotImage(
                uuid_str=spot_result.image.uuid,
                thumbnail=spot_result.image.thumbnail,
                url=spot_result.image.url,
                title=spot_result.image.title,
                reference_id=db_picture.id,
                meta_data=spot_result.image.meta_data
            )
            db_spot = DBSpot(
                uuid_str=spot_result.uuid,
                address=spot_result.address,
                name=spot_result.name,
                rating=spot_result.rating,
                rating_n=spot_result.rating_n,
                place_id=spot_result.place_id,
                reference=spot_result.reference,
                types=spot_result.types,
                geometry=spot_result.geometry,
                spot_image_id=db_picture.id
            )
            db_spot.spot_image = db_spot_img
            db.add(db_spot)
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
        "spot_id":    spot_result.uuid,
        "created_at": spot_result.created_at,
        "address":    spot_result.address,
        "name":       spot_result.name,
        "rating":     spot_result.rating,
        "rating_n":   spot_result.rating_n,
        "place_id":   spot_result.place_id,
        "reference":  spot_result.reference,
        "types":      spot_result.types,
        "geometry":   spot_result.geometry,
        "image": {
            "id":  spot_result.image.uuid,
            "url": spot_result.image.thumbnail
        }
    }
    resp = JSONResponse(
        status_code=200,
        content=jsonable_encoder(raw_resp)
    )

    app_logger.info(
        "endpoint: /v1/spots/search, info: done request for searching spot with picture %s",
        s3_pic_id
    )

    return resp


@app.get("/v1/spots/{spot_id}/nearby")
async def get_near_spots_by_spot(
        spot_id: str,
        db: Session = Depends(db_main.get_db_session)
):

    """
    get_near_spot_by_spot: search for near by spots by a given spot
    curl -XGET 'http://0.0.0.0:5000/v1/spots/8c820169-e26e-474f-a603-981bfd3121c1/nearby'
    """

    app_logger.info(
        "endpoint: /v1/spots/{spot_id}/nearby, info: get request for searching nearby spots for spot %s",
        spot_id
    )

    err_status_code = 500
    err_type = "FailedToProcessRequest"
    try:

        # check spot_id
        if (spot_id is None) or (len(spot_id) == 0):
            err_status_code = 400
            err_type = "InvalidRequest"
            raise Exception("failed to parse spot_id")

        # get spot from db
        db_spot = db.get(DBSpot, spot_id)
        if (db_spot is None) or (len(db_spot.url) == 0):
            err_status_code = 404
            err_type = "InvalidRequest"
            raise Exception(f"spot {spot_id} not found in database")

        # nearby spot search
        svr_spot = model_utils.db_spot_to_server_spot(db_spot)
        svr_nearby_spot_list = spot_logics.search_nearby_spots_by_spot(
            api_key=app_params['serpapi_api_key'],
            spot=svr_spot
        )
        app_logger.info("found %d nearby spot(s) for spot %s", len(svr_nearby_spot_list), spot_id)

        # prepare result
        res_spot_list = []
        for svr_nearby_spot in svr_nearby_spot_list:

            res_spot = {
                "spot_id":    svr_nearby_spot.uuid,
                "created_at": svr_nearby_spot.created_at,
                "address":    svr_nearby_spot.address,
                "name":       svr_nearby_spot.name,
                "rating":     svr_nearby_spot.rating,
                "rating_n":   svr_nearby_spot.rating_n,
                "place_id":   svr_nearby_spot.place_id,
                "reference":  svr_nearby_spot.reference,
                "types":      svr_nearby_spot.types,
                "geometry":   svr_nearby_spot.geometry,
            }
            res_spot_list.append(res_spot)

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

    raw_resp = {"spots": res_spot_list}
    resp = JSONResponse(
        status_code=200,
        content=jsonable_encoder(raw_resp)
    )
    app_logger.info(
        "endpoint: /v1/spots/{spot_id}/nearby, info: done request for searching nearby spots for spot %s",
        spot_id
    )

    return resp


if __name__ == '__main__':

    uvicorn.run(
        app=app,
        host=app_params['app_host'],
        port=int(app_params['app_port']),
        log_level=app_logger.level
    )
