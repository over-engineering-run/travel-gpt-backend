import os
import sys

from typing import Annotated

from fastapi import Header, HTTPException

_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root_dir)

from servers.utils import init as server_init


app_params, app_resources, app_logger = server_init.init_server()


async def verify_token(authorization: Annotated[str, Header()]):
    if authorization != f"Basic {app_params['app_auth_token']}":
        raise HTTPException(status_code=401, detail="header invalid")
