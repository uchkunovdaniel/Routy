"""Same demo data as seed() in frontend/src/lib/api.js. Inserted only into an empty database."""

from sqlalchemy import Engine
from sqlmodel import Session, select

from models import Review, Route, User
from security import demo_password_hash

USERS = [
    {"id": "u1", "name": "Мария", "email": "maria@example.com"},
    {"id": "u2", "name": "Георги", "email": "georgi@example.com"},
]

ROUTES = [
    {
        "id": "r1", "author_id": "u1", "title": "Седемте рилски езера за един ден",
        "destination": "Рила, България", "created_at": "2026-08-14",
        "impressions": "Най-красивата гледка е от върха над Окото. Тръгнахме рано и бяхме сами до Бъбрека.",
        "tips": "Вземете връхна дреха – духа дори през август. Лифтът затваря в 17:00.",
        "waypoints": [
            {"name": "Хижа Рилски езера", "lat": 42.2086, "lng": 23.3222},
            {"name": "Окото", "lat": 42.2033, "lng": 23.3189},
            {"name": "Бъбрека", "lat": 42.2008, "lng": 23.3156},
            {"name": "Езерен връх", "lat": 42.1969, "lng": 23.3111},
        ],
        "reviews": [
            {"id": "v1", "user_id": "u2", "user_name": "Георги", "rating": 5,
             "text": "Точно както е описано. Благодаря за съветите!", "created_at": "2026-09-02"},
        ],
    },
    {
        "id": "r2", "author_id": "u2", "title": "Черни връх по билото от Алеко",
        "destination": "Витоша, България", "created_at": "2026-07-03",
        "impressions": "Лесен маршрут с широк изглед към София. Мъглата се спуска бързо след обяд.",
        "tips": "Тръгвайте преди 9 ч. и проверете прогнозата за гръмотевици.",
        "waypoints": [
            {"name": "Алеко", "lat": 42.5631, "lng": 23.2897},
            {"name": "Резньовете", "lat": 42.5547, "lng": 23.2736},
            {"name": "Черни връх", "lat": 42.5617, "lng": 23.2744},
        ],
        "reviews": [
            {"id": "v2", "user_id": "u1", "user_name": "Мария", "rating": 4,
             "text": "Хубав маршрут, но има много хора в събота.", "created_at": "2026-07-20"},
        ],
    },
    {
        "id": "r3", "author_id": "u1", "title": "Родопска приказка: Триград и Дяволското гърло",
        "destination": "Родопи, България", "created_at": "2026-06-21",
        "impressions": "Пещерата е впечатляваща, а ждрелото – прохладно убежище в жегата.",
        "tips": "Обувки с добро сцепление – пътеката е мокра. Опитайте пъстърва в Триград.",
        "waypoints": [
            {"name": "Триград", "lat": 41.6075, "lng": 24.3731},
            {"name": "Ждрелото", "lat": 41.6139, "lng": 24.3631},
            {"name": "Дяволско гърло", "lat": 41.6153, "lng": 24.3589},
        ],
        "reviews": [],
    },
]


def seed_if_empty(engine: Engine) -> None:
    with Session(engine) as session:
        if session.exec(select(User).limit(1)).first() is not None:
            return
        pw = demo_password_hash()
        for u in USERS:
            session.add(User(**u, password_hash=pw))
        # The mock keeps routes newest-first and unshifts new ones, so insert seeds in
        # reverse to keep "later seq = earlier in the mock's array".
        for r in reversed(ROUTES):
            data = {k: v for k, v in r.items() if k != "reviews"}
            session.add(Route(**data, photos=[]))
            for v in reversed(r["reviews"]):
                session.add(Review(route_id=r["id"], **v))
        session.commit()
