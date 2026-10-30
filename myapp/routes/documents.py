from pathlib import Path
from urllib.parse import quote
from uuid import UUID, uuid4

from fastapi import APIRouter, Cookie, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from myapp.database.database import get_db
from myapp.database.models import Document, Notebook, NotebookQA, OCRChunk, User
from myapp.routes.auth import bearer_scheme, get_current_user


router = APIRouter(prefix="/dashboard/notebooks", tags=["documents"])
templates = Jinja2Templates(directory="templates")

UPLOAD_ROOT = Path("uploads")
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".txt"}


def _browser_user(
    credentials: HTTPAuthorizationCredentials | None,
    cookie_token: str | None,
    db: Session,
) -> User | None:
    try:
        return get_current_user(credentials, cookie_token, db)
    except HTTPException:
        return None


def _notebook_redirect(notebook_id: UUID, message: str) -> RedirectResponse:
    return RedirectResponse(
        f"/dashboard/notebooks/{notebook_id}?message={quote(message)}",
        status_code=303,
    )


def _owned_notebook(db: Session, notebook_id: UUID, user: User) -> Notebook | None:
    return db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == user.id,
    ).first()


def _index_text(db: Session, document: Document, text: str) -> None:
    if not text.strip():
        return
    from langchain_core.documents import Document as TextDocument

    from myapp.services.chunking.doc_chunking import create_chunks
    from myapp.services.search.chunks_2_db import save_chunks

    source_page = TextDocument(page_content=text, metadata={"page_number": 1})
    save_chunks(db, document.id, create_chunks([source_page]))


def _process_uploaded_document(db: Session, document: Document, path: Path) -> None:
    if path.suffix.lower() == ".txt":
        text = path.read_text(encoding="utf-8-sig")
        document.total_pages = 1
        db.commit()
        _index_text(db, document, text)
        return

    from langchain_core.documents import Document as TextDocument

    from myapp.ocr.ocr_service import kannada_ocr

    result = kannada_ocr.process_file(str(path))
    document.total_pages = result.total_pages
    document.average_confidence = result.average_confidence
    document.classification = result.document_classification
    db.commit()
    pages = [
        TextDocument(page_content=page.raw_text, metadata={"page_number": page.page_number})
        for page in result.pages
    ]
    if pages:
        from myapp.services.chunking.doc_chunking import create_chunks
        from myapp.services.search.chunks_2_db import save_chunks

        save_chunks(db, document.id, create_chunks(pages))


@router.post("/{notebook_id}/questions")
def ask_notebook(
    notebook_id: UUID,
    request: Request,
    question: str = Form(...),
    document_ids: list[UUID] = Form(default=[]),
    response_language: str = Form("en"),
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
    question = question.strip()
    if response_language not in {"en", "hi", "kn"}:
        response_language = "en"
    if not question:
        return _notebook_redirect(notebook.id, "Enter a question")

    # Only accept source IDs that belong to this notebook. An empty selection
    # means all sources in the notebook.
    selected_ids = {
        document.id
        for document in notebook.documents
        if not document_ids or document.id in document_ids
    }
    if document_ids and (not selected_ids or len(selected_ids) != len(document_ids)):
        return _notebook_redirect(notebook.id, "Choose at least one source from this notebook")

    has_chunks_query = (
        db.query(OCRChunk)
        .join(Document, OCRChunk.document_id == Document.id)
        .filter(Document.notebook_id == notebook.id)
    )
    if document_ids:
        has_chunks_query = has_chunks_query.filter(Document.id.in_(selected_ids))
    has_chunks = has_chunks_query.first()
    if not has_chunks:
        return templates.TemplateResponse(
            request=request,
            name="notebook.html",
            context={
                "user": user,
                "notebook": notebook,
                "question": question,
                "message": "Add a text or processed document source before asking questions.",
                "selected_document_ids": selected_ids,
                "conversation": list(
                    reversed(
                        db.query(NotebookQA)
                        .filter_by(notebook_id=notebook.id)
                        .order_by(NotebookQA.created_at.desc())
                        .limit(100)
                        .all()
                    )
                ),
                "selected_document_ids": selected_ids,
            },
        )
    try:
        from myapp.services.response.llm_vector_response import answer_question

        answer = answer_question(
            db=db,
            query=question,
            user_id=user.id,
            notebook_id=notebook.id,
            filter_parameter={"document_ids": list(selected_ids)} if document_ids else None,
            response_language=response_language,
        )
        qa = NotebookQA(
            notebook_id=notebook.id,
            question=question,
            answer=str(answer),
            document_ids=[str(document_id) for document_id in selected_ids]
            if document_ids else [],
        )
        db.add(qa)
        db.commit()
    except Exception:
        return templates.TemplateResponse(
            request=request,
            name="notebook.html",
            context={
                "user": user,
                "notebook": notebook,
                "question": question,
                "message": "Could not answer right now. Check the AI and embedding configuration, then try again.",
                "selected_document_ids": selected_ids,
                "conversation": list(
                    reversed(
                        db.query(NotebookQA)
                        .filter_by(notebook_id=notebook.id)
                        .order_by(NotebookQA.created_at.desc())
                        .limit(100)
                        .all()
                    )
                ),
                "selected_document_ids": selected_ids,
            },
            status_code=503,
        )
    return templates.TemplateResponse(
        request=request,
        name="notebook.html",
        context={
            "user": user,
            "notebook": notebook,
            "conversation": list(
                reversed(
                    db.query(NotebookQA)
                    .filter_by(notebook_id=notebook.id)
                    .order_by(NotebookQA.created_at.desc())
                    .limit(100)
                    .all()
                )
            ),
            "selected_document_ids": selected_ids,
        },
    )


@router.post("/{notebook_id}/sources")
@router.post("/{notebook_id}/documents", include_in_schema=False)
def upload_document(
    notebook_id: UUID,
    file: UploadFile = File(...),
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

    original_name = Path(file.filename or "").name
    suffix = Path(original_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        return _notebook_redirect(notebook.id, "Upload a PDF, image, or UTF-8 text file.")
    content = file.file.read(MAX_UPLOAD_BYTES + 1)
    if not content:
        return _notebook_redirect(notebook.id, "Choose a file before uploading.")
    if len(content) > MAX_UPLOAD_BYTES:
        return _notebook_redirect(notebook.id, "Files must be 20 MB or smaller.")

    target_dir = UPLOAD_ROOT / str(user.id) / str(notebook.id)
    target_dir.mkdir(parents=True, exist_ok=True)
    stored_path = target_dir / f"{uuid4().hex}{suffix}"
    stored_path.write_bytes(content)

    document = Document(
        notebook_id=notebook.id,
        filename=original_name[:255],
        file_path=str(stored_path),
        mime_type=file.content_type,
        file_size=len(content),
        total_pages=0,
    )
    db.add(document)
    try:
        db.commit()
        db.refresh(document)
        _process_uploaded_document(db, document, stored_path)
    except UnicodeDecodeError:
        db.rollback()
        if document.id:
            db.query(Document).filter(Document.id == document.id).delete()
            db.commit()
        stored_path.unlink(missing_ok=True)
        return _notebook_redirect(notebook.id, "Text files must use UTF-8 encoding.")
    except Exception:
        db.rollback()
        if document.id:
            db.query(Document).filter(Document.id == document.id).delete()
            db.commit()
        stored_path.unlink(missing_ok=True)
        return _notebook_redirect(
            notebook.id,
            "Could not process that source. Check OCR and embedding configuration.",
        )
    return _notebook_redirect(notebook.id, "Source added to notebook.")


@router.post("/{notebook_id}/text-sources")
def add_pasted_text(
    notebook_id: UUID,
    title: str = Form(...),
    pasted_text: str = Form(...),
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

    title = title.strip() or "Copied text"
    pasted_text = pasted_text.strip()
    if not pasted_text:
        return _notebook_redirect(notebook.id, "Paste some text first")
    content = pasted_text.encode("utf-8")
    if len(content) > MAX_UPLOAD_BYTES:
        return _notebook_redirect(notebook.id, "Text must be 20 MB or smaller")

    target_dir = UPLOAD_ROOT / str(user.id) / str(notebook.id)
    target_dir.mkdir(parents=True, exist_ok=True)
    stored_path = target_dir / f"{uuid4().hex}.txt"
    stored_path.write_bytes(content)
    safe_title = Path(title).name[:250].strip() or "Copied text"
    filename = safe_title if safe_title.lower().endswith(".txt") else f"{safe_title}.txt"
    document = Document(
        notebook_id=notebook.id,
        filename=filename[:255],
        file_path=str(stored_path),
        mime_type="text/plain; charset=utf-8",
        file_size=len(content),
        total_pages=1,
    )
    db.add(document)
    try:
        db.commit()
        db.refresh(document)
        _index_text(db, document, pasted_text)
    except Exception:
        db.rollback()
        if document.id:
            db.query(Document).filter(Document.id == document.id).delete()
            db.commit()
        stored_path.unlink(missing_ok=True)
        return _notebook_redirect(notebook.id, "Could not index that text")
    return _notebook_redirect(notebook.id, "Text added as a source")
