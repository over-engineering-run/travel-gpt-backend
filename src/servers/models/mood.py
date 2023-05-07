import datetime
import uuid


class MoodMessage:

    def __init__(
            self,
            uuid_str: str = None,
            created_at: datetime.datetime = None,
            content: str = None,
            prompt: str = None,
            model: str = None,
    ):

        self.uuid       = uuid_str or str(uuid.uuid4())
        self.created_at = created_at or datetime.datetime.now()
        self.content    = content
        self.prompt     = prompt
        self.model      = model


class MoodPicture:

    def __init__(
            self,
            uuid_str: str = None,
            created_at: datetime.datetime = None,
            url: str = None,
            size: str = None,
            prompt: str = None,
            model: str = None,
    ):

        self.uuid       = uuid_str or str(uuid.uuid4())
        self.created_at = created_at or datetime.datetime.now()
        self.url        = url
        self.size       = size
        self.prompt     = prompt
        self.model      = model
