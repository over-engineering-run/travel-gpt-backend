import os
import sys

import json

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
from servers.logics import picture as pic_logics

from databases import database as db_main
from databases.models.mood import MoodPicture as DBMoodPicture
from databases.models.picture import Picture as DBPicture


router = APIRouter(
    prefix="/v1/pictures"
)


@router.get("/{s3_pic_id}")
async def get_picture(
        s3_pic_id: str,
        db: Session = Depends(db_main.get_db_session)
):

    """
    get_picture: get s3 picture info from by id
    curl -XGET 'http://0.0.0.0:5000/v1/pictures/d1e82e9f-bc4f-4a97-991b-0e37d50dd6c9'
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


@router.post("")
@router.post("/")
async def post_picture(
        req_body: dict,
        db: Session = Depends(db_main.get_db_session)
):

    """
    post_picture: save picture to s3
    curl -XPOST 'http://0.0.0.0:5000/v1/pictures' -H 'Content-Type: application/json' -d '{"type": "mood_pic", "id": "3cb3c712-0b16-49b5-b181-9ee8012f7fc1"}'
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
