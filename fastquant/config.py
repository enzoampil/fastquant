import os
from pkg_resources import resource_filename
from pathlib import Path

DATA_PATH = resource_filename(__name__, "data")

if not Path(DATA_PATH).exists():
    os.makedirs(DATA_PATH)
