# Standard Library
import time
from contextlib import contextmanager

import docker
from sqlalchemy import create_engine

from geoai import config

CONTAINER_NAME = "geoai_postgres"


def start_container():
    remove_container()
    client = docker.from_env()
    pg_data_dir_host = config.POSTGRES_DATA_DIR.absolute()
    pg_data_dir_container = "/var/lib/postgresql/data"
    volumes = {pg_data_dir_host: {"bind": pg_data_dir_container, "mode": "rw"}}
    client.containers.run(
        "postgis/postgis",
        auto_remove=True,
        remove=True,
        detach=True,
        name=CONTAINER_NAME,
        environment=[
            "POSTGRES_HOST_AUTH_METHOD=trust",
            f"PGDATA={pg_data_dir_container}",
            f"POSTGRES_USER={config.POSTGRES_USER}",
            f"POSTGRES_DB={config.POSTGRES_DB_NAME}",
        ],
        ports={5432: config.POSTGRES_PORT},
        volumes=volumes,
        shm_size="1G",
    )

    # Wait for the time container fully starts
    time.sleep(10)


def check_container():
    client = docker.from_env()
    assert len(client.containers.list(filters={"name": CONTAINER_NAME})) < 2
    return len(client.containers.list(filters={"name": CONTAINER_NAME})) == 1


def remove_container():
    client = docker.from_env()
    containers = client.containers.list(all=True, filters={"name": CONTAINER_NAME})
    for container in containers:
        container.remove(force=True)


def ensure_container():
    if not check_container():
        start_container()


@contextmanager
def get_engine():
    ensure_container()
    engine = create_engine(
        f"postgresql://{config.POSTGRES_USER}:@localhost:{config.POSTGRES_PORT}/{config.POSTGRES_DB_NAME}",
        pool_size=100,
        max_overflow=0,
    )
    yield engine
    engine.dispose()


@contextmanager
def get_connection():
    with get_engine() as engine:
        yield engine.connect()


def main():
    start_container()


if __name__ == "__main__":
    main()
