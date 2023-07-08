import datetime
import uuid


class Picture:

    """model for saving picture on s3"""

    def __init__(
            self,
            uuid_str:   str = None,
            created_at: datetime.datetime = None,
            filename:   str = None,
            size:       str = None,
            url:        str = None,
            found_spot: bool = None
    ):

        time_now        = datetime.datetime.now()
        timestamp_str   = time_now.strftime("%Y%m%d-%s")

        self.uuid       = uuid_str or str(uuid.uuid4())
        self.created_at = created_at or time_now
        self.filename   = filename or f'{timestamp_str}.{self.uuid}.png'
        self.size       = size
        self.url        = url
        self.found_spot = found_spot

        self.meta_data = {
            "ref_id":   None,
            "ref_type": None,  # 'mood_pic'
        }
