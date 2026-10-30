from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from myapp.database import models
from myapp.database.database import engine
from myapp.routes.auth import router as auth_router
from myapp.routes.dashboard import router as dashboard_router
from myapp.routes.documents import router as documents_router

app = FastAPI(title="Kannada OCR")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(documents_router)
models.Base.metadata.create_all(engine)
# create_all() creates missing tables, but does not add columns to existing ones.
with engine.begin() as connection:
    connection.execute(
        text(
            "ALTER TABLE users "
            "ADD COLUMN IF NOT EXISTS auth_token_version INTEGER NOT NULL DEFAULT 0"
        )
    )

@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse(url="/dashboard", status_code=303)
