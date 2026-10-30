# Kannada Notebook LM

A web app for organizing document sources into notebooks, extracting Kannada text from scans, and asking questions grounded in selected sources. It supports PDF, image, UTF-8 text, and pasted-text sources, cross-language questions, saved notebook Q&A, speech input/output, and light/dark themes.

## Features

- User registration, login, and logout with signed access tokens.
- Private notebooks containing uploaded or pasted sources.
- Kannada OCR for scanned PDFs and images using Tesseract, with Gemini used for handwriting or low-confidence OCR.
- Text chunking, multilingual embeddings, vector similarity search, and reranking.
- Questions can be limited to selected notebook documents; successful question/answer pairs are saved in notebook history.
- Answers can be requested in English, Hindi, or Kannada.
- Browser speech recognition and speech synthesis controls.
- Responsive notebook and dashboard pages with persisted language and theme preferences.

## Stack

- Python, FastAPI, SQLAlchemy, Jinja2
- PostgreSQL with the `pgvector` extension
- Google Gemini through LangChain
- Hugging Face `intfloat/multilingual-e5-base` embeddings and `BAAI/bge-reranker-v2-m3` reranking
- Tesseract OCR, Pillow, OpenCV, and PyMuPDF
- Plain HTML, CSS, and JavaScript

## Requirements

- Python 3.10 or newer
- PostgreSQL with pgvector installed and enabled
- Tesseract OCR installed with Kannada language data (`kan.traineddata`)
- A Google AI API key for Gemini handwriting OCR and question answering
- Internet access on first use to download the embedding and reranker models

On Windows, install Tesseract and ensure `tesseract.exe` is on `PATH`, or set `TESSERACT_CMD` to its full path. Install the Kannada trained data into Tesseract's `tessdata` directory. On Debian/Ubuntu, the relevant system packages are commonly `tesseract-ocr` and `tesseract-ocr-kan`; install PostgreSQL and the pgvector package for your PostgreSQL version as well.

## Setup

### 1. Create a PostgreSQL database

Create a database and enable pgvector in it:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

For example, from `psql` connected to your app database:

```bash
psql -d kannada_notebook -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and set the database URL, a random secret key of at least 32 characters, and your Google AI API key. Keep `.env` private and never commit it.

```env
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/kannada_notebook
SECRET_KEY=replace-with-a-random-secret-at-least-32-characters-long
GOOGLE_API_KEY=replace-with-your-google-ai-api-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_ALGORITHM=HS256
COOKIE_SECURE=false
TESSERACT_CMD=tesseract
OCR_LANGUAGE=kan
OCR_ENGINE_MODE=1
OCR_PAGE_SEGMENTATION=6
```

`COOKIE_SECURE=false` is appropriate for local HTTP development. Set it to `true` behind HTTPS in production. `TESSERACT_CMD` can be set to a full executable path, such as `C:\Program Files\Tesseract-OCR\tesseract.exe`.

### 4. Run the app

From the repository root, with the virtual environment activated:

```bash
uvicorn main:app --reload
```

Open <http://127.0.0.1:8000>. FastAPI's interactive API documentation is at <http://127.0.0.1:8000/docs>.

The app calls SQLAlchemy `create_all()` at startup to create missing tables and applies the existing `auth_token_version` column compatibility statement. `create_all()` does not migrate changes to already existing tables; use a database migration when the schema evolves beyond adding new tables.

## Run with Docker

Build the image from the repository root:

```bash
docker build -t kannada-notebook-lm .
```

The image includes Tesseract and Kannada language data. Pass the required settings through an environment file and persist uploaded files and Hugging Face model downloads in Docker volumes:

```bash
docker run --rm --name kannada-notebook-lm \
  --env-file .env \
  -p 8000:8000 \
  -v kannada_uploads:/app/uploads \
  -v kannada_hf_cache:/home/app/.cache/huggingface \
  kannada-notebook-lm
```

If PostgreSQL runs directly on the host, set `DATABASE_URL` in `.env` to use `host.docker.internal` instead of `localhost` (for example, `postgresql+psycopg2://user:password@host.docker.internal:5432/kannada_notebook`). If PostgreSQL runs in another container, put both containers on the same Docker network and use the database container or service name as the host. Enable pgvector in the database before starting the app.

The container listens on port `8000`. Open <http://127.0.0.1:8000> on the host.

## Use

1. Register an account and sign in.
2. Create a notebook.
3. Add a PDF, image, UTF-8 `.txt` file, or pasted text.
4. Wait for OCR and embedding to finish. The first file that needs embeddings may trigger large model downloads; avoid restarting the development server during that first download.
5. Select one or more source checkboxes in the left panel, then ask a question. If no sources are selected, retrieval uses all sources in the notebook.
6. Select English, Hindi, or Kannada in the header to set the response language.

The microphone and read-aloud buttons use browser speech APIs. Microphone access requires browser permission, and support varies by browser. Use a recent Chrome or Edge over localhost or HTTPS for speech recognition.

## Project layout

```text
main.py                         FastAPI app and router registration
myapp/config/                   Environment settings and Gemini client
myapp/database/                 SQLAlchemy models and database session
myapp/routes/                   Authentication, dashboard, and document routes
myapp/ocr/                      Kannada OCR and document preprocessing
myapp/services/chunking/        Text splitting
myapp/services/embeddings/      Hugging Face embeddings
myapp/services/search/          Vector retrieval and chunk persistence
myapp/services/reranking/       Cross-encoder reranking
myapp/services/response/        Context formatting and LLM answers
templates/                      Jinja2 pages
static/css/                     Page styles
static/js/                      Browser interactions and speech controls
static/images/                  UI icons
uploads/                        User-uploaded files (runtime data, not source)
```

## Data and operations

- Uploaded documents are stored under `uploads/<user-id>/<notebook-id>/`; document metadata, OCR chunks, vectors, and Q&A history are stored in PostgreSQL.
- Back up the PostgreSQL database and `uploads/` together if you need to preserve notebook data.
- Model weights are cached by Hugging Face in the current user's cache directory. The cache can be large.
- Do not expose the development server directly to the public internet. Use HTTPS, secure cookies, managed secrets, and a production ASGI deployment for hosted use.

## Troubleshooting

- **Missing database configuration:** verify that `.env` exists in the project root and contains `DATABASE_URL` and `SECRET_KEY`.
- **pgvector type or extension error:** install pgvector for PostgreSQL and run `CREATE EXTENSION IF NOT EXISTS vector;` in the app database.
- **Tesseract executable not found:** install Tesseract and set `TESSERACT_CMD` to its executable path.
- **Kannada language data missing:** install `kan.traineddata` into Tesseract's `tessdata` directory and make sure `OCR_LANGUAGE=kan`.
- **Gemini requests fail:** check `GOOGLE_API_KEY`, network access, and provider quota.
- **First upload is slow:** embedding and reranking models are downloaded on first use. Let the download finish before restarting the server.
- **Static changes do not appear:** hard refresh the browser; versioned static asset URLs are used for cache busting where needed.

## Development notes

There is no automated test suite configured in this repository yet. Keep uploaded files, local model caches, virtual environments, secrets, and generated Python files out of version control.
