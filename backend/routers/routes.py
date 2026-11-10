import math
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, col, select

from db import get_session
from models import Review, Route, User
from routers.auth import CurrentUser
from sanitize import clean, safe_image, valid_coords
from schemas import ReviewIn, RouteIn, RouteOut
from services import decorate

router = APIRouter(prefix="/api/routes", tags=["routes"])

SessionDep = Annotated[Session, Depends(get_session)]

MSG_ROUTE_NOT_FOUND = "Маршрутът не съществува."
MSG_TOO_FEW_POINTS = "Добавете поне две точки от маршрута на картата."
MSG_TITLE_REQUIRED = "Заглавието и дестинацията са задължителни."
MSG_OWN_ROUTE = "Не можете да оценявате собствен маршрут."
MSG_EMPTY_REVIEW = "Напишете няколко думи в отзива."
MSG_NOT_OWNER = "Можете да променяте само собствените си маршрути."
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


def _validated_fields(body: RouteIn) -> dict:
    """Port of createRoute()'s validation, shared by create and edit. Same check order as the mock."""
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

    return {
        "title": title,
        "destination": destination,
        "waypoints": waypoints,
        "impressions": clean(body.impressions, 4000),
        "tips": clean(body.tips, 2000),
        "photos": [p for p in map(safe_image, body.photos) if p][:MAX_PHOTOS],
    }


@router.post("", response_model=RouteOut, status_code=status.HTTP_201_CREATED)
def create_route(body: RouteIn, user: CurrentUser, session: SessionDep):
    route = Route(author_id=user.id, created_at=today(), **_validated_fields(body))
    session.add(route)
    session.commit()
    session.refresh(route)
    return decorate(session, route)

def _own_route_or_403(session: Session, route_id: str, user: User) -> Route:
    route = _get_route_or_404(session, route_id)
    if route.author_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, MSG_NOT_OWNER)
    return route


@router.put("/{route_id}", response_model=RouteOut)
def update_route(route_id: str, body: RouteIn, user: CurrentUser, session: SessionDep):
    """Full replace of the editable fields. Author, createdAt and reviews are kept."""
    route = _own_route_or_403(session, route_id, user)
    for field, value in _validated_fields(body).items():
        setattr(route, field, value)
    session.add(route)
    session.commit()
    session.refresh(route)
    return decorate(session, route)


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_route(route_id: str, user: CurrentUser, session: SessionDep) -> None:
    route = _own_route_or_403(session, route_id, user)
    for review in session.exec(select(Review).where(Review.route_id == route.id)).all():
        session.delete(review)
    session.delete(route)
    session.commit()


def js_round(x: float) -> int:
    """JS Math.round: halves round up (2.5 -> 3, -2.5 -> -2), unlike Python's banker's rounding."""
    return math.floor(x + 0.5)


@router.post("/{route_id}/reviews", response_model=RouteOut)
def add_review(route_id: str, body: ReviewIn, user: CurrentUser, session: SessionDep):
    """Port of addReview(): one review per user per route, the newest replaces the old one."""
    route = _get_route_or_404(session, route_id)
    if route.author_id == user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, MSG_OWN_ROUTE)
    text = clean(body.text, 1000)
    if not text:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, MSG_EMPTY_REVIEW)
    stars = min(5, max(1, js_round(body.rating)))

    for old in session.exec(
        select(Review).where(Review.route_id == route.id, Review.user_id == user.id)
    ).all():
        session.delete(old)
    session.add(Review(
        route_id=route.id, user_id=user.id, user_name=user.name,
        rating=stars, text=text, created_at=today(),
    ))
    session.commit()
    return decorate(session, route)
