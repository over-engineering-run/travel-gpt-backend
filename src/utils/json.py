import uuid
import datetime


def json_serializer(obj):

    if isinstance(obj, datetime.datetime):
        return obj.isoformat()  # obj.strftime("%Y-%m-%dT%H:%M:%SZ")
    elif isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, uuid.UUID):
        return str(obj)
    else:
        return obj.__dict__

    raise TypeError("Type not serializable")
