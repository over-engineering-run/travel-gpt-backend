import os
import sys
import logging

import openai
from wrapt_timeout_decorator import timeout

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

from utils import s3 as s3_utils
from utils import misc as misc_utils

from servers.models import picture as pic_models

_RETRY = 1
_TIMEOUT = 10.0


@timeout(_TIMEOUT)
def _upload_picture_to_s3(
        source_url: str,
        filename: str,
        s3_region: str,
        s3_bucket_name: str,
        s3_file_path: str,
):

    return s3_utils.s3_upload_fileobj_by_url(
        source_url=source_url,
        s3_region=s3_region,
        s3_bucket_name=s3_bucket_name,
        s3_file_path=s3_file_path,
        filename=filename,
    )

def save_picture_to_s3_by_url(
        source_url: str,
        source_size: str,
        s3_region: str,
        s3_bucket_name: str,
        s3_file_path: str,
) -> pic_models.Picture:

    logging.info("uploading picture to s3: %s", source_url)

    pic = pic_models.Picture(
        size=source_size,
    )

    s3_http_url = misc_utils.retry(
        retry_n=_RETRY,
        _func=_upload_picture_to_s3,
        source_url=source_url,
        filename=pic.filename,
        s3_region=s3_region,
        s3_bucket_name=s3_bucket_name,
        s3_file_path=s3_file_path,
    )
    pic.url = s3_http_url

    logging.info("done upload picture to %s ", pic.url)

    return pic
