import os
import sys

import datetime
import uuid

from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy import func

_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root_dir)

from databases.database import Base


class SpotImage(Base):

    __tablename__ = 'spot_images'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    thumbnail = db.Column(db.String)
    url = db.Column(db.String)
    title = db.Column(db.String)
    reference_id = db.Column(UUID(as_uuid=True))
    meta_data = db.Column(JSONB)

    spot = relationship('Spot', back_populates="spot_image")

    def __init__(
            self,
            uuid_str: str = None,
            thumbnail: str = None,
            url: str = None,
            title: str = None,
            reference_id: str = None,
            meta_data: dict = None,
    ):

        self.id           = uuid_str or str(uuid.uuid4())
        self.thumbnail    = thumbnail
        self.url          = url
        self.title        = title
        self.reference_id = reference_id
        self.meta_data    = meta_data


class Spot(Base):

    __tablename__ = 'spots'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    address = db.Column(db.String)
    name = db.Column(db.String)
    rating = db.Column(db.Float)
    rating_n = db.Column(db.Integer)
    place_id = db.Column(db.String)
    reference = db.Column(db.String)
    types = db.Column(ARRAY(db.String))
    geometry = db.Column(JSONB)

    spot_image_id = db.Column(UUID(as_uuid=True), db.ForeignKey("spot_images.id"))
    spot_image = relationship('SpotImage', back_populates="spot")

    def __init__(
            self,
            uuid_str: str = None,
            address: str = None,
            name: str = None,
            rating: float = None,
            rating_n: int = None,
            place_id: str = None,
            reference: str = None,
            types: list[str] = None,
            geometry: dict = None,
            spot_image_id: str = None
    ):

        self.id            = uuid_str or str(uuid.uuid4())
        self.address       = address
        self.name          = name
        self.rating        = rating
        self.rating_n      = rating_n
        self.place_id      = place_id
        self.reference     = reference
        self.spot_image_id = spot_image_id

        if types is not None:
            self.types = types

        if geometry is not None:
            self.geometry = geometry
