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
from servers.models.error import ErrorInfo
from servers.utils import model as model_utils
from servers.logics import spot as spot_logics

from databases import database as db_main
from databases.models.picture import Picture as DBPicture
from databases.models.spot import SpotImage as DBSpotImage
from databases.models.spot import Spot as DBSpot


router = APIRouter(
    prefix="/v1/spots"
)


@router.get("/search")
async def get_spot_search_by_picture(
        s3_pic_id: str,
        db: Session = Depends(db_main.get_db_session)
):

    """
    get_spot_search_by_picture: search spot by s3 picture
    curl -XGET 'http://0.0.0.0:5000/v1/spots/search?s3_pic_id=d1e82e9f-bc4f-4a97-991b-0e37d50dd6c9'
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

        if (db_picture.found_spot is False):
            resp = JSONResponse(
                status_code=404,
                content={"message": f"no spot found for s3 picture {s3_pic_id}"}
            )
            return resp

        # try to get from cache
        db_spot_list = db.query(DBSpot) \
                    .filter(
                        DBSpot.spot_image.reference_id == db_picture.id
                    ).order_by(
                        desc(DBSpot.spot_image.created_at)
                    ).all()

        for db_spot in db_spot_list:

            if (db_spot is not None) and \
               (db_spot.spot_image is not None) and \
               (db_spot.spot_image.thumbnail is not None) and \
               (len(db_spot.spot_image.thumbnail) > 0) and \
               (db_spot.spot_image.thumbnail.strip().startswith('http')):

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
                        "id":  db_spot.spot_image.id,
                        "url": db_spot.spot_image.thumbnail,
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

        # TODO: resolve worker timeout
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

            # TODO: resolve worker timeout
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

            resp = JSONResponse(
                status_code=404,
                content={"message": f"no spot found for s3 picture {s3_pic_id}"}
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


@router.get("/{spot_id}/nearby")
async def get_near_spots_by_spot(
        spot_id: str,
        db: Session = Depends(db_main.get_db_session)
):

    """
    get_near_spot_by_spot: search for near by spots by a given spot
    curl -XGET 'http://0.0.0.0:5000/v1/spots/5d9b7970-5567-48fd-85f4-3a29080b2c38/nearby'
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
        if (db_spot is None) or (len(db_spot.name) == 0):
            err_status_code = 404
            err_type = "InvalidRequest"
            raise Exception(f"spot {spot_id} not found in database")

        # TODO: resolve worker timeout
        # nearby spot search
        svr_spot = model_utils.db_spot_to_server_spot(db_spot)
        svr_nearby_spot_list = spot_logics.search_nearby_spots_by_spot(
            api_key=app_params['google_api_key'],
            spot=svr_spot,
            logger=app_logger
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
