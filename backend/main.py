import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import database_url, init_db, make_engine
from routers import auth, routes


def cors_origins() -> list[str]:
    # Comma-separated; defaults to the Vite dev server.
    raw = os.environ.get("ROUTY_CORS_ORIGINS", "http://localhost:5173")
    return [o.strip() for o in raw.split(",") if o.strip()]


def create_app(db_url: str | None = None) -> FastAPI:
    engine = make_engine(db_url or database_url())

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        init_db(engine)
        yield
        engine.dispose()

    app = FastAPI(title="Routy API", lifespan=lifespan)
    app.state.engine = engine
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins(),
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(auth.router)
    app.include_router(routes.router)

    @app.get("/")
    async def root():
        return {"status": "ok"}

    return app


app = create_app()
