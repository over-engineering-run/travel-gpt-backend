import os
import sys

import datetime
import uuid

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import func

_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root_dir)

from databases.database import Base


class Picture(Base):

    __tablename__ = 'pictures'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    filename = db.Column(db.String)
    size = db.Column(db.String)
    url = db.Column(db.String)
    reference_type = db.Column(db.String)
    reference_id = db.Column(UUID(as_uuid=True))

    def __init__(
            self,
            uuid_str: str = None,
            filename: str = None,
            size: str = None,
            url: str = None,
            reference_type: str = None,
            reference_id: str = None,
    ):

        self.id             = uuid_str or str(uuid.uuid4())
        self.filename       = filename
        self.size           = size
        self.url            = url
        self.reference_type = reference_type
        self.reference_id   = reference_id
