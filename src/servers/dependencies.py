import os
import sys

_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root_dir)

from servers.utils import init as server_init


app_params, app_resources, app_logger = server_init.init_server()
