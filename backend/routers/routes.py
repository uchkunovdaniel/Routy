from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, col, select

from db import get_session
from models import Route
from routers.auth import CurrentUser
from sanitize import clean, safe_image, valid_coords
from schemas import RouteIn, RouteOut
from services import decorate

router = APIRouter(prefix="/api/routes", tags=["routes"])

SessionDep = Annotated[Session, Depends(get_session)]

MSG_ROUTE_NOT_FOUND = "Маршрутът не съществува."
MSG_TOO_FEW_POINTS = "Добавете поне две точки от маршрута на картата."
MSG_TITLE_REQUIRED = "Заглавието и дестинацията са задължителни."
MAX_PHOTOS = 6


def today() -> str:
    # Same as the mock's new Date().toISOString().slice(0, 10) (UTC date).
    return datetime.now(UTC).date().isoformat()


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


@router.post("", response_model=RouteOut, status_code=status.HTTP_201_CREATED)
def create_route(body: RouteIn, user: CurrentUser, session: SessionDep):
    """Port of createRoute(). Checks run in the same order as the mock."""
    points = [p for p in body.waypoints if isinstance(p, dict) and valid_coords(p.get("lat"), p.get("lng"))]
    waypoints = [
        {"name": clean(p.get("name"), 80) or f"Точка {i + 1}", "lat": p["lat"], "lng": p["lng"]}
        for i, p in enumerate(points)
    ]
    if len(waypoints) < 2:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, MSG_TOO_FEW_POINTS)

    title = clean(body.title, 120)
    destination = clean(body.destination, 120)
    if not title or not destination:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, MSG_TITLE_REQUIRED)

    route = Route(
        author_id=user.id,
        title=title,
        destination=destination,
        waypoints=waypoints,
        impressions=clean(body.impressions, 4000),
        tips=clean(body.tips, 2000),
        photos=[p for p in map(safe_image, body.photos) if p][:MAX_PHOTOS],
        created_at=today(),
    )
    session.add(route)
    session.commit()
    session.refresh(route)
    return decorate(session, route)
