import os
import sys
import logging

import openai
from wrapt_timeout_decorator import timeout

_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root_dir)

from utils import s3 as s3_utils
from utils import misc as misc_utils

from servers.models import mood as mood_models


_MSG_RETRY = 2
_MSG_TIMEOUT = 10.0

_MSG_PROMPT = """
Help me tp generate a random easy-to-understand sentence to describe my mood.
""".strip()

_IMG_RETRY = 1
_IMG_TIMEOUT = 30.0

_IMG_PROMPT = """
some tourist spot that reflect my mood which is
""".strip()


@timeout(_MSG_TIMEOUT)
def _openai_random_mood_message_create(
        model: str,
        prompt: str,
        n: int
):

    openai_response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=50,
        temperature=2
    )

    msg_str = openai_response.choices[0]['message']['content'].strip()

    if ('AI' in msg_str) or ('computer' in msg_str):
        logging.warning(msg_str)
        raise Exception('model not generating mood message')

    msg_str = msg_str.strip('\"').strip('\'')

    return msg_str


def generate_random_mood_message(
        model: str
) -> mood_models.MoodMessage:

    mood_message = misc_utils.retry(
        retry_n=_MSG_RETRY,
        _func=_openai_random_mood_message_create,
        model=model,
        prompt=_MSG_PROMPT,
        n=1,
    )

    return mood_message


@timeout(_IMG_TIMEOUT)
def _openai_image_create(prompt: str, size: str, n: int):
    return openai.Image.create(
        prompt=prompt, size=size, n=n,
    )


def generate_mood_image_by_description(
        mood_msg: mood_models.MoodMessage,
        image_size: str,
) -> mood_models.MoodPicture:

    """
    generate image based on mood message and update picture
    """

    # openai generate image
    logging.info("generating image from mood: %s", mood_msg.content)

    prompt = f"{_IMG_PROMPT} {mood_msg.content}"
    openai_response = misc_utils.retry(
        retry_n=_IMG_RETRY,
        _func=_openai_image_create,
        prompt=prompt,
        size=image_size,
        n=1,
    )

    # parsing response
    logging.info("parsing response from openai")

    data_list = openai_response.get('data')
    if len(data_list) == 0:
        raise Exception("faied to generate picture from mood %s", mood_msg.content)
    data = data_list[0]

    # result
    if data.get('url') is None:
        raise Exception("faied to generate picture from mood %s", mood_msg.content)

    mood_pic = mood_models.MoodPicture(
        url=data.get('url'),
        size=image_size,
        model="DALLE",
        prompt=prompt,
    )

    logging.info("done generated images from mood message")

    return mood_pic
