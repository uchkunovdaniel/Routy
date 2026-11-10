from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, col, select

from db import get_session
from models import Route
from schemas import RouteOut
from services import decorate

router = APIRouter(prefix="/api/routes", tags=["routes"])

SessionDep = Annotated[Session, Depends(get_session)]

MSG_ROUTE_NOT_FOUND = "Маршрутът не съществува."


def _get_route_or_404(session: Session, route_id: str) -> Route:
    route = session.exec(select(Route).where(Route.id == route_id)).first()
    if route is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, MSG_ROUTE_NOT_FOUND)
    return route


@router.get("", response_model=list[RouteOut])
def list_routes(session: SessionDep, q: str = "", sort: str = "new", author: str | None = None):
    """Port of listRoutes(). `author` filters by authorId (what the Profile page needs)."""
    stmt = select(Route).order_by(col(Route.seq).desc())  # mock array order: newest first
    if author:
        stmt = stmt.where(Route.author_id == author)
    routes = [decorate(session, r) for r in session.exec(stmt).all()]

    term = q.strip().lower()
    if term:
        routes = [r for r in routes if term in f"{r.title} {r.destination}".lower()]

    # Python's sort is stable like JS's, so ties keep the newest-first order above.
    if sort == "top":
        routes.sort(key=lambda r: (r.rating, r.rating_count), reverse=True)
    else:
        routes.sort(key=lambda r: r.created_at, reverse=True)
    return routes


@router.get("/{route_id}", response_model=RouteOut)
def get_route(route_id: str, session: SessionDep):
    return decorate(session, _get_route_or_404(session, route_id))
