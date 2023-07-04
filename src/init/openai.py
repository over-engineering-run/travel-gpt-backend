import os
import sys

import logging

import openai

_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root_dir)

from utils import misc as misc_utils


def init_openai(api_org, api_key, retry_n=1):

    """init openai and check connection with retry"""

    openai.organization = api_org
    openai.api_key      = api_key

    _ = misc_utils.retry(retry_n=retry_n, _func=openai.Model.list)
