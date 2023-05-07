import datetime
import uuid


class SpotImage:

    """spot image found with google len"""

    def __init__(
            self,
            uuid_str:   str = None,
            created_at: datetime.datetime = None,
            thumbnail:  str = None,
            url:        str = None,
            title:      str = None,
    ):
        self.uuid         = uuid_str or str(uuid.uuid4())
        self.created_at   = created_at or datetime.datetime.now()
        self.thumbnail    = thumbnail
        self.url          = url
        self.title        = title

        self.meta_data    = {
            'position':   None,
            'src_domain': None,
            'src_url':    None,
        }


class Spot:

    """spot found with google map"""

    def __init__(
            self,
            uuid_str:   str = None,
            created_at: datetime.datetime = None,
            address:    str = None,
            name:       str = None,
            rating:     float = None,
            rating_n:   int = None,
            place_id:   str = None,
            reference:  str = None,
            types:      list[str] = None,
            geometry:   dict = None,
            image:      SpotImage = None,
    ):
        self.uuid       = uuid_str or str(uuid.uuid4())
        self.created_at = created_at or datetime.datetime.now()

        self.address    = address
        self.name       = name
        self.rating     = rating
        self.rating_n   = rating_n
        self.place_id   = place_id   # from google map
        self.reference  = reference  # from google map
        self.types      = types
        self.geometry   = geometry

        self.image      = image
