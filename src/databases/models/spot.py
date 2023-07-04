import os
import sys

import datetime
import uuid

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy import func

_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root_dir)

from databases.database import Base


class SpotImage(Base):

    __tablename__ = 'spot_images'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    thumbnail = Column(String)
    url = Column(String)
    title = Column(String)
    reference_id = Column(UUID(as_uuid=True))
    meta_data = Column(JSONB)

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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    address = Column(String)
    name = Column(String)
    rating = Column(Float)
    rating_n = Column(Integer)
    place_id = Column(String)
    reference = Column(String)
    types = Column(ARRAY(String))
    geometry = Column(JSONB)

    spot_image_id = Column(UUID(as_uuid=True), ForeignKey("spot_images.id"))
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
