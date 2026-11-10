import secrets
import string

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

_ALPHABET = string.ascii_lowercase + string.digits


def new_id() -> str:
    """8-char base36 id, same shape as the frontend mock's uid()."""
    return "".join(secrets.choice(_ALPHABET) for _ in range(8))


# `seq` is an insertion counter. It reproduces the mock's array order
# (newest first) as a tie-breaker when sorting.


class User(SQLModel, table=True):
    seq: int | None = Field(default=None, primary_key=True)
    id: str = Field(default_factory=new_id, unique=True, index=True)
    name: str
    email: str = Field(unique=True, index=True)
    password_hash: str


class Route(SQLModel, table=True):
    seq: int | None = Field(default=None, primary_key=True)
    id: str = Field(default_factory=new_id, unique=True, index=True)
    author_id: str = Field(index=True)
    title: str
    destination: str
    created_at: str  # "YYYY-MM-DD", like the frontend
    impressions: str = ""
    tips: str = ""
    waypoints: list[dict] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    photos: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))


class Review(SQLModel, table=True):
    seq: int | None = Field(default=None, primary_key=True)
    id: str = Field(default_factory=new_id, unique=True, index=True)
    route_id: str = Field(index=True)
    user_id: str = Field(index=True)
    user_name: str
    rating: int
    text: str
    created_at: str
