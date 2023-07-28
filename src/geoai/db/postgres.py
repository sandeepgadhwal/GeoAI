from geoai import config
from sqlalchemy import create_engine
import docker


def start_container():
    remove_container()
    client = docker.from_env()
    client.containers.run(
        "postgis/postgis", 
        auto_remove=True,
        remove=True,
        detach=True,
        name='geoai_postgres',
        environment=[
            "POSTGRES_HOST_AUTH_METHOD=trust",
            f"PGDATA={config.POSTGRES_DATA_DIR}",
            f"POSTGRES_USER={config.POSTGRES_USER}",
            f"POSTGRES_DB={config.POSTGRES_DB_NAME}"
        ],
        ports={5432: config.POSTGRES_PORT}
    )

def check_container():
    client = docker.from_env()
    assert len(client.containers.list(filters={"name": 'geoai_postgres'})) < 2
    return len(client.containers.list(filters={"name": 'geoai_postgres'})) == 1


def remove_container():
    client = docker.from_env()
    return [container.remove(force=True) for container in client.containers.list(all=True, filters={"name": 'geoai_postgres'})]

def ensure_container():
    if not check_container():
        start_container()

def get_engine():
    ensure_container()
    # return create_engine('postgresql+psycopg2://user:password@hostname/database_name', pool_size=20, max_overflow=0)
    return create_engine(f'postgresql://{config.POSTGRES_USER}:@localhost:{config.POSTGRES_PORT}/{config.POSTGRES_DB_NAME}', pool_size=20, max_overflow=0)

# def get_conection():
#     get_engine()