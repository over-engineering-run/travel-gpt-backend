import os
import sys

import datetime
import uuid

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import func

_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root_dir)

from databases.database import Base


class MoodMessage(Base):

    __tablename__ = 'mood_messages'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    content = Column(String)
    prompt = Column(String)
    model = Column(String)
    cached = Column(Boolean, default=False)

    def __init__(
            self,
            uuid_str: str = None,
            content: str = None,
            prompt: str = None,
            model: str = None,
            cached: bool = False
    ):
        self.id      = uuid_str or str(uuid.uuid4())
        self.content = content
        self.prompt  = prompt
        self.model   = model
        self.cached  = cached


class MoodPicture(Base):

    __tablename__ = 'mood_pictures'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    url = Column(String)
    size = Column(String)
    prompt = Column(String)
    model = Column(String)

    mood_message_id = Column(UUID(as_uuid=True), ForeignKey("mood_messages.id"))

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
