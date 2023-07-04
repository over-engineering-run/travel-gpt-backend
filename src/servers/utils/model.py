import os
import sys

import logging
import argparse

_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root_dir)

from databases.models.mood import MoodMessage as DBMoodMessage
from databases.models.mood import MoodPicture as DBMoodPicture
from databases.models.picture import Picture as DBPicture
from databases.models.spot import SpotImage as DBSpotImage
from databases.models.spot import Spot as DBSpot

from servers.models.mood import MoodMessage as SvrMoodMessage
from servers.models.mood import MoodPicture as SvrMoodPicture
from servers.models.picture import Picture as SvrPicture
from servers.models.spot import SpotImage as SvrSpotImage
from servers.models.spot import Spot as SvrSpot


def db_mood_message_to_server_mood_message(db_mood_message: DBMoodMessage) -> SvrMoodMessage:

    svr_mood_message = SvrMoodMessage(
        uuid_str=db_mood_message.id,
        created_at=db_mood_message.created_at,
        content=db_mood_message.content,
        prompt=db_mood_message.prompt,
        model=db_mood_message.model,
        cached=db_mood_message.cached
    )
    return svr_mood_message


def db_mood_picture_to_server_mood_picture(db_mood_pic: DBMoodPicture) -> SvrMoodPicture:

    svr_mood_pic = SvrMoodPicture(
        uuid_str=db_mood_pic.id,
        created_at=db_mood_pic.created_at,
        url=db_mood_pic.url,
        size=db_mood_pic.size,
        prompt=db_mood_pic.prompt,
        model=db_mood_pic.model,
    )
    return svr_mood_pic


def db_picture_to_server_picture(db_picture: DBPicture) -> SvrPicture:

    svr_picture = SvrPicture(
        uuid_str=db_picture.id,
        filename=db_picture.filename,
        url=db_picture.url,
        size=db_picture.size,
        created_at=db_picture.created_at
    )
    return svr_picture


def db_spot_img_to_server_spot_img(db_spot_img: DBSpotImage) -> SvrSpotImage:

    if db_spot_img is None:
        return None

    svr_spot_img = SvrSpotImage(
        uuid_str=db_spot_img.id,
        created_at=db_spot_img.created_at,
        thumbnail=db_spot_img.thumbnail,
        url=db_spot_img.url,
        title=db_spot_img.title
    )
    return svr_spot_img


def db_spot_to_server_spot(db_spot: DBSpot) -> SvrSpot:

    svr_spot = SvrSpot(
        uuid_str=db_spot.id,
        created_at=db_spot.created_at,
        address=db_spot.address,
        name=db_spot.name,
        rating=db_spot.rating,
        rating_n=db_spot.rating_n,
        place_id=db_spot.place_id,
        reference=db_spot.reference,
        types=db_spot.types,
        geometry=db_spot.geometry,
        image=db_spot_img_to_server_spot_img(db_spot.spot_image)
    )
    return svr_spot
