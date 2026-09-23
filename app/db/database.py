from collections.abc import Iterator
from pathlib import Path

from fastapi import Request
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session


def create_database_engine(database_url: str) -> Engine:
    path = Path(make_url(database_url).database).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        make_url(database_url).set(database=str(path)),
        connect_args={"check_same_thread": False, "timeout": 10},
    )

    @event.listens_for(engine, "connect")
    def register_casefold(connection, _record):
        # SQLite lower()/NOCASE are ASCII-only; support Russian search too.
        connection.create_function("casefold", 1, str.casefold, deterministic=True)

    return engine


def get_session(request: Request) -> Iterator[Session]:
    with Session(request.app.state.engine) as session:
        yield session
