import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from db import get_session
from models import User
from sanitize import clean
from schemas import AuthOut, LoginIn, RegisterIn, UserOut
from security import create_token, hash_password, read_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

SessionDep = Annotated[Session, Depends(get_session)]

_EMAIL = re.compile(r"\S+@\S+\.\S+")
_bearer = HTTPBearer(auto_error=False)

MSG_REGISTER_INVALID = "Попълнете име, валиден имейл и парола от поне 6 символа."
MSG_EMAIL_TAKEN = "Вече има акаунт с този имейл."
MSG_BAD_LOGIN = "Грешен имейл или парола."
# Not in the mock (it had no tokens); only seen when calling protected endpoints logged out.
MSG_UNAUTHORIZED = "Моля, влезте в профила си."


def current_user(
    session: SessionDep,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    user_id = read_token(creds.credentials) if creds else None
    user = session.exec(select(User).where(User.id == user_id)).first() if user_id else None
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, MSG_UNAUTHORIZED, headers={"WWW-Authenticate": "Bearer"}
        )
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def _auth_out(user: User) -> AuthOut:
    return AuthOut(user=UserOut(id=user.id, name=user.name, email=user.email), token=create_token(user.id))


@router.post("/register", response_model=AuthOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, session: SessionDep):
    name = clean(body.name, 40)
    email = clean(body.email, 120).lower()
    if not name or not _EMAIL.fullmatch(email) or len(body.password) < 6:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, MSG_REGISTER_INVALID)
    if session.exec(select(User).where(User.email == email)).first():
        raise HTTPException(status.HTTP_409_CONFLICT, MSG_EMAIL_TAKEN)
    user = User(name=name, email=email, password_hash=hash_password(body.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return _auth_out(user)


@router.post("/login", response_model=AuthOut)
def login(body: LoginIn, session: SessionDep):
    email = clean(body.email, 120).lower()
    user = session.exec(select(User).where(User.email == email)).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, MSG_BAD_LOGIN)
    return _auth_out(user)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return UserOut(id=user.id, name=user.name, email=user.email)
