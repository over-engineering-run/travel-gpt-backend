import os
import sys

import datetime
import uuid

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import func

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

from databases.databases import db


class MoodMessage(db.Model):

    __tablename__ = 'mood_messages'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    content = db.Column(db.String)
    prompt = db.Column(db.String)
    model = db.Column(db.String)

    def __init__(
            self,
            uuid_str: str = None,
            content: str = None,
            prompt: str = None,
            model: str = None,
    ):
        self.id      = uuid_str or str(uuid.uuid4())
        self.content = content
        self.prompt  = prompt
        self.model   = model


class MoodPicture(db.Model):

    __tablename__ = 'mood_pictures'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    url = db.Column(db.String)
    size = db.Column(db.String)
    prompt = db.Column(db.String)
    model = db.Column(db.String)

    mood_message_id = db.Column(UUID(as_uuid=True), db.ForeignKey("mood_messages.id"))

    def __init__(
            self,
            uuid_str: str = None,
            url: str = None,
            size: str = None,
            prompt: str = None,
            model: str = None,
            mood_message_id: str = None,
    ):

        self.id     = uuid_str or str(uuid.uuid4())
        self.url    = url
        self.size   = size
        self.prompt = prompt
        self.model  = model

        self.mood_message_id = mood_message_id
