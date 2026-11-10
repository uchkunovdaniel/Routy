from contextlib import asynccontextmanager

from fastapi import FastAPI

from db import database_url, init_db, make_engine
from seed import seed_if_empty


def create_app(db_url: str | None = None) -> FastAPI:
    engine = make_engine(db_url or database_url())

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        init_db(engine)
        seed_if_empty(engine)
        yield
        engine.dispose()

    app = FastAPI(title="Routy API", lifespan=lifespan)
    app.state.engine = engine

    @app.get("/")
    async def root():
        return {"status": "ok"}

    return app


app = create_app()
