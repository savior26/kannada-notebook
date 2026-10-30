from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from fastapi import APIRouter, Cookie, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.templating import Jinja2Templates
from pwdlib import PasswordHash
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from myapp.config.settings import settings
from myapp.database.database import get_db
from myapp.database.models import User
from myapp.schema import LoginRequest, TokenResponse, UserCreate, UserResponse


router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)
templates = Jinja2Templates(directory="templates")
password_hash = PasswordHash.recommended()


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def _credentials_error(detail: str = "Could not validate credentials") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _issue_access_token(user: User) -> TokenResponse:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = jwt.encode(
        {"sub": str(user.id), "ver": user.auth_token_version, "iat": now, "exp": expires},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return TokenResponse(
        access_token=token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/register_user", response_model=UserResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def register(request: UserCreate, db: Session = Depends(get_db)) -> User:
    email = str(request.email).strip().lower()
    user = User(email=email, hashed_password=get_password_hash(request.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists") from exc
    db.refresh(user)
    return user


@router.get("/register", response_class=HTMLResponse, include_in_schema=False)
def registration_page(request: Request, error: str | None = None):
    return templates.TemplateResponse(
        request=request, name="auth/register.html", context={"error": error}
    )


@router.post("/register", include_in_schema=False)
def register_from_page(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    email = email.strip().lower()
    if len(password) < 4 or len(password) > 8:
        return templates.TemplateResponse(
            request=request, name="auth/register.html",
            context={"error": "Password must be between 4 and 8 characters.", "email": email},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    if password != confirm_password:
        return templates.TemplateResponse(
            request=request, name="auth/register.html",
            context={"error": "The passwords do not match.", "email": email},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    try:
        UserCreate(email=email, password=password)
    except ValidationError:
        return templates.TemplateResponse(
            request=request, name="auth/register.html",
            context={"error": "Enter a valid email address.", "email": email},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    try:
        user = User(email=email, hashed_password=get_password_hash(password))
        db.add(user)
        db.commit()
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse(
            request=request, name="auth/register.html",
            context={"error": "An account with that email already exists.", "email": email},
            status_code=status.HTTP_409_CONFLICT,
        )
    return RedirectResponse(url="/auth/login?registered=1", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
def login_page(request: Request, error: str | None = None, registered: bool = False):
    return templates.TemplateResponse(
        request=request, name="auth/login.html",
        context={"error": error, "registered": registered},
    )


@router.post("/login", include_in_schema=False)
def login_from_page(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if user is None or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            request=request, name="auth/login.html",
            context={"error": "Email or password is incorrect.", "email": email},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    token = _issue_access_token(user)
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token", value=token.access_token, httponly=True,
        # Secure cookies are ignored by browsers on local plain-HTTP development.
        secure=settings.COOKIE_SECURE and request.url.scheme == "https",
        samesite="lax", path="/",
    )
    return response


@router.post("/token", response_model=TokenResponse)
def create_token(credentials: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """JSON token endpoint for API clients; browser users use the login page."""
    user = db.query(User).filter(User.email == str(credentials.email).strip().lower()).first()
    if user is None or not verify_password(credentials.password, user.hashed_password):
        raise _credentials_error("Invalid email or password")
    return _issue_access_token(user)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    cookie_token: str | None = Cookie(default=None, alias="access_token"),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials if credentials else cookie_token
    if not token:
        raise _credentials_error()
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require": ["sub", "exp", "ver"]},
        )
        user_id = UUID(payload["sub"])
        token_version = payload["ver"]
        if not isinstance(token_version, int):
            raise ValueError("Invalid token version")
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise _credentials_error() from exc

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or user.auth_token_version != token_version:
        raise _credentials_error()
    return user


@router.get("/authentication", response_model=UserResponse, include_in_schema=False)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/logout", include_in_schema=False)
def logout_from_page(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Access tokens are otherwise stateless; bumping the version revokes all sessions.
    current_user.auth_token_version += 1
    db.commit()
    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token", path="/")
    return response
