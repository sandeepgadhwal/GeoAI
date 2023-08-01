# Standard Library
import os
from pathlib import Path

WORK_DIR = Path(os.path.expanduser("~/.GeoAI"))

POSTGRES_DATA_DIR = WORK_DIR / "pgdata"
POSTGRES_USER = "postgres"
POSTGRES_PORT = 54320
POSTGRES_DB_NAME = "geoai"
