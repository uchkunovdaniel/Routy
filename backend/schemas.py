"""Request/response shapes. JSON is camelCase to match frontend/src/lib/api.js."""

from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class UserOut(CamelModel):
    id: str
    name: str
    email: str


class AuthOut(CamelModel):
    user: UserOut
    token: str


class Waypoint(CamelModel):
    name: str
    lat: float
    lng: float


class ReviewOut(CamelModel):
    id: str
    user_id: str
    user_name: str
    rating: int
    text: str
    created_at: str


class RouteOut(CamelModel):
    id: str
    author_id: str
    author: str
    title: str
    destination: str
    created_at: str
    impressions: str
    tips: str
    waypoints: list[Waypoint]
    photos: list[str]
    reviews: list[ReviewOut]
    rating: float
    rating_count: int


# Inputs: missing fields default to empty so the server answers with the same
# Bulgarian validation messages as the mock instead of a generic 422.


class RegisterIn(CamelModel):
    name: str = ""
    email: str = ""
    password: str = ""


class LoginIn(CamelModel):
    email: str = ""
    password: str = ""


class RouteIn(CamelModel):
    title: str = ""
    destination: str = ""
    impressions: str = ""
    tips: str = ""
    # Loosely typed on purpose: invalid points/photos are dropped, not rejected (as in the mock).
    waypoints: list[Any] = Field(default_factory=list)
    photos: list[Any] = Field(default_factory=list)


class ReviewIn(CamelModel):
    rating: Annotated[float, Field(allow_inf_nan=False)]
    text: str = ""
