from sqlmodel import Session, col, select

from models import Review, Route, User
from schemas import ReviewOut, RouteOut, Waypoint


def decorate(session: Session, route: Route) -> RouteOut:
    """Port of decorate() in api.js: adds author name, rating average and count."""
    reviews = session.exec(
        select(Review).where(Review.route_id == route.id).order_by(col(Review.seq).desc())
    ).all()
    author = session.exec(select(User).where(User.id == route.author_id)).first()
    n = len(reviews)
    return RouteOut(
        id=route.id,
        author_id=route.author_id,
        author=author.name if author else "Непознат",
        title=route.title,
        destination=route.destination,
        created_at=route.created_at,
        impressions=route.impressions,
        tips=route.tips,
        waypoints=[Waypoint(**w) for w in route.waypoints],
        photos=route.photos,
        reviews=[
            ReviewOut(
                id=v.id, user_id=v.user_id, user_name=v.user_name,
                rating=v.rating, text=v.text, created_at=v.created_at,
            )
            for v in reviews
        ],
        rating=sum(v.rating for v in reviews) / n if n else 0,
        rating_count=n,
    )
