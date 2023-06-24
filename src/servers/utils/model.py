import os
import sys

import logging
import argparse

_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root_dir)

from databases.models.mood import MoodMessage as DBMoodMessage
from databases.models.mood import MoodPicture as DBMoodPicture
from databases.models.picture import Picture as DBPicture

from servers.models.mood import MoodMessage as SvrMoodMessage
from servers.models.mood import MoodPicture as SvrMoodPicture
from servers.models.picture import Picture as SvrPicture


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
