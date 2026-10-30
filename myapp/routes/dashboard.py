from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, selectinload

from myapp.database.database import get_db
from myapp.database.models import Notebook, NotebookQA, User
from myapp.routes.auth import bearer_scheme, get_current_user
from myapp.utils.time import format_india_time


router = APIRouter(prefix="/dashboard", tags=["dashboard"])
templates = Jinja2Templates(directory="templates")
templates.env.filters["india_time"] = format_india_time

def _browser_user(
    credentials: HTTPAuthorizationCredentials | None,
    cookie_token: str | None,
    db: Session,
) -> User | None:
    try:
        return get_current_user(credentials, cookie_token, db)
    except HTTPException:
        return None


def _dashboard_redirect(message: str | None = None) -> RedirectResponse:
    if message:
        url = f"/dashboard?message={quote(message)}"
    else:
        url = "/dashboard"
    return RedirectResponse(url, status_code=303)


def _notebook_redirect(notebook_id: UUID, message: str) -> RedirectResponse:
    return RedirectResponse(
        f"/dashboard/notebooks/{notebook_id}?message={quote(message)}",
        status_code=303,
    )


def _owned_notebook(db: Session, notebook_id: UUID, user: User) -> Notebook | None:
    return (
        db.query(Notebook)
        .options(selectinload(Notebook.documents))
        .filter(Notebook.id == notebook_id, Notebook.user_id == user.id)
        .first()
    )


@router.get("")
def dashboard(
    request: Request,
    message: str | None = None,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    cookie_token: str | None = Cookie(default=None, alias="access_token"),
    db: Session = Depends(get_db),
):
    user = _browser_user(credentials, cookie_token, db)
    if user is None:
        return RedirectResponse("/auth/login", status_code=303)

    notebooks = (
        db.query(Notebook)
        .options(selectinload(Notebook.documents))
        .filter(Notebook.user_id == user.id)
        .order_by(Notebook.updated_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "user": user,
            "display_name": user.email.partition("@")[0],
            "notebooks": notebooks,
            "message": message,
        },
    )


@router.post("/notebooks")
def create_notebook(
    title: str = Form(...),
    description: str = Form(""),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    cookie_token: str | None = Cookie(default=None, alias="access_token"),
    db: Session = Depends(get_db),
):
    user = _browser_user(credentials, cookie_token, db)
    if user is None:
        return RedirectResponse("/auth/login", status_code=303)
    title = title.strip()
    if not title or len(title) > 255:
        return _dashboard_redirect("Notebook title must be between 1 and 255 characters.")

    notebook = Notebook(
        user_id=user.id,
        title=title,
        description=description.strip() or None,
    )
    db.add(notebook)
    db.commit()
    return _dashboard_redirect("Notebook created.")


@router.get("/notebooks/{notebook_id}")
def notebook_page(
    notebook_id: UUID,
    request: Request,
    message: str | None = None,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    cookie_token: str | None = Cookie(default=None, alias="access_token"),
    db: Session = Depends(get_db),
):
    user = _browser_user(credentials, cookie_token, db)
    if user is None:
        return RedirectResponse("/auth/login", status_code=303)
    notebook = _owned_notebook(db, notebook_id, user)
    if notebook is None:
        raise HTTPException(status_code=404, detail="Notebook not found")
    return templates.TemplateResponse(
        request=request,
        name="notebook.html",
        context={
            "user": user,
            "notebook": notebook,
            "message": message,
            "conversation": list(
                reversed(
                    db.query(NotebookQA)
                    .filter_by(notebook_id=notebook.id)
                    .order_by(NotebookQA.created_at.desc())
                    .limit(100)
                    .all()
                )
            ),
        },
    )


