import os
import sys

_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root_dir)

from databases.database import Base, engine


def init_db():
    Base.metadata.create_all(bind=engine)
