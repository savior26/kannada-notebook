# PROJECT NAME : Kannada Notebook LM

## Problem Statement : Kannada Text Digitization

## Description 
A web app for organizing documents into private notebooks, extracting Kannada text from scans, and asking questions grounded in selected sources. Sources can be PDFs, images, UTF-8 text files, or pasted text. The app supports English, Hindi, and Kannada answers, saved notebook Q&A, and browser speech input/output.

## Testing & Demo Access

The application is deployed live on Render and supports self-registration. You do not need pre-configured credentials to test the features.

### Live Application
🔗 *[Live Demo](https://kannada-notebook-123.onrender.com)*

### How to Test:
1. Open the *[Live Demo](https://kannada-notebook-123.onrender.com)* link.
2. Navigate to the *Sign Up* / *Register* page.
3. Create a new account using any email and password or use test credentials: Email: `xyz@xyz.in`, Password: `xyz@xyz`.
5. Log in and explore the application features.

> *Note:* Initial load times may take 30–50 seconds if the Render instance is waking up from a free-tier sleep state.

## Features

- User registration, login, and logout using signed JWT cookies.
- Private notebooks and document uploads.
- Kannada OCR for scanned PDFs and images using Tesseract; Gemini can transcribe handwriting and assist with low-confidence OCR.
- Text chunking, Jina AI embeddings, PostgreSQL/pgvector similarity search, and source filtering.
- Gemini-powered question answering grounded in retrieved notebook sources.
- Responsive dashboard and notebook pages with language and theme preferences.

## Technology

- Python 3.10+
- FastAPI, Uvicorn, Jinja2, SQLAlchemy, and Pydantic
- A Supabase project with PostgreSQL and the `vector` (pgvector) extension enabled
- Google Gemini via LangChain
- Jina AI Embeddings API
- Tesseract OCR with Kannada language data, Pillow, OpenCV, NumPy, and PyMuPDF
- HTML, CSS, and JavaScript

## Prerequisites

- Python 3.10 or newer
- A Supabase project with access to its PostgreSQL database
- Tesseract OCR installed with Kannada language data (`kan.traineddata`)
- A Google AI API key for Gemini
- Jina AI API credentials for vector embeddings

On Windows, add `tesseract.exe` to `PATH` or set `TESSERACT_CMD` to its full path. On Debian or Ubuntu, the Tesseract packages are commonly named `tesseract-ocr` and `tesseract-ocr-kan`.

## Setup

### 1. Configure the Supabase database

Create a project in Supabase, then enable pgvector in its database. In the Supabase Dashboard, open **SQL Editor** and run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Get the PostgreSQL connection string from your project’s **Connect** panel. Use the **direct connection** for a long-running server when its network supports the endpoint’s IP version. If your host is IPv4-only, use Supabase’s **session pooler** connection string instead. Copy the connection string supplied by Supabase rather than constructing the pooler host or username yourself. Replace its password placeholder and URL-encode reserved characters in the password.

For this FastAPI/SQLAlchemy app, set `DATABASE_URL` to the Supabase URI and use the `postgresql+psycopg://` SQLAlchemy dialect prefix. Keep the host, port, username, database name, and password from the Supabase-provided string. Require SSL by adding `?sslmode=require` (or `&sslmode=require` if the URI already has query parameters).

### 2. Create a virtual environment and install dependencies

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

Copy `.env.example` to `.env` and provide your database URL, a random secret of at least 32 characters, Google AI API key, and Jina API settings. Keep `.env` private and do not commit it.

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@YOUR_SUPABASE_HOST:5432/postgres?sslmode=require
SECRET_KEY=replace-with-a-random-secret-at-least-32-characters-long
GOOGLE_API_KEY=your-google-ai-api-key
JINA_API_URL=https://api.jina.ai/v1/embeddings
JINA_MODEL=jina-embeddings-v3
JINA_API_KEY=your-jina-api-key

ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_ALGORITHM=HS256
COOKIE_SECURE=false

TESSERACT_CMD=tesseract
OCR_LANGUAGE=kan
OCR_ENGINE_MODE=1
OCR_PAGE_SEGMENTATION=6
```

Replace the example Supabase host, port, and password with the values in your project’s **Connect** panel; pooled connection strings have a different host, port, and username. `DATABASE_URL` uses the `psycopg` driver. Keep it secret and configure it in the deployment environment as well as your local `.env`. `COOKIE_SECURE=false` is suitable for local HTTP development; enable it when serving the app over HTTPS. `TESSERACT_CMD` can be a full path, for example `C:\Program Files\Tesseract-OCR\tesseract.exe`.

### 4. Start the app

From the repository root with the virtual environment active:

```bash
uvicorn main:app --reload
```

Open <http://127.0.0.1:8000>. Interactive API documentation is at <http://127.0.0.1:8000/docs>.

At startup, the app creates missing tables and applies a compatibility statement for the `users.auth_token_version` column. SQLAlchemy `create_all()` does not migrate other schema changes to existing tables; use database migrations as the schema evolves.

## Docker

Build the image from the repository root:

```bash
docker build -t kannada-notebook-lm .
```

Run it with the required settings from `.env`:

```bash
docker run --rm --name kannada-notebook-lm \
  --env-file .env \
  -p 8000:8000 \
  kannada-notebook-lm
```

The image installs Tesseract and Kannada language data. The container connects to Supabase over the network using `DATABASE_URL`; make sure the deployment can reach the selected Supabase endpoint and that the URL uses SSL. Enable pgvector in Supabase before starting the app.

## Using the app

1. Register and sign in.
2. Create a notebook.
3. Add a PDF, image, UTF-8 `.txt` file, or pasted text.
4. Wait for OCR and embedding to finish. Embeddings are generated by the configured Jina API, so uploads require network access and valid Jina credentials.
5. Select source checkboxes and ask a question. With no sources selected, retrieval uses all documents in the notebook.
6. Choose English, Hindi, or Kannada as the answer language.

Microphone and read-aloud controls use browser speech APIs. Microphone access requires browser permission. Speech recognition support varies by browser; a recent Chrome or Edge on localhost or HTTPS is recommended.

## Project layout

```text
main.py                              FastAPI application and router registration
myapp/config/                        Application settings and Gemini client
myapp/database/                      SQLAlchemy models and database session
myapp/routes/                        Authentication, dashboard, and document routes
myapp/ocr/                           Kannada OCR and document preprocessing
myapp/vector_service/chunking/       Text splitting
myapp/vector_service/embeddings/     Jina embedding API client
myapp/vector_service/vector_store/   Vector persistence and retrieval
myapp/vector_service/response/       Context formatting and LLM answers
templates/                           Jinja2 pages
static/                              CSS, JavaScript, and UI images
```

## Data and operations

- Original uploads are processed from temporary files and discarded after their chunks are saved.
- PostgreSQL stores document metadata, OCR text chunks, vectors, and notebook Q&A history.
- Back up PostgreSQL to preserve notebook sources and their searchable content.
- Do not expose the development server directly to the public internet. For hosted use, configure HTTPS, secure cookies, managed secrets, and a production ASGI deployment.

## Troubleshooting

- **Missing database or secret configuration:** make sure `.env` exists in the repository root and defines `DATABASE_URL` and a `SECRET_KEY` of at least 32 characters.
- **Supabase connection fails:** verify `DATABASE_URL` matches the connection method selected in Supabase’s **Connect** panel, the database password is URL-encoded if it contains reserved characters, and SSL is enabled. For IPv4-only hosts, try the Supabase session pooler.
- **pgvector type or extension error:** run `CREATE EXTENSION IF NOT EXISTS vector;` in the Supabase SQL Editor for this project’s database.
- **Tesseract executable not found:** install Tesseract and set `TESSERACT_CMD` to its executable path.
- **Kannada language data missing:** install `kan.traineddata` and confirm `OCR_LANGUAGE=kan`.
- **Gemini requests fail:** check `GOOGLE_API_KEY`, internet access, and provider quota.
- **Embedding requests fail:** check `JINA_API_URL`, `JINA_MODEL`, `JINA_API_KEY`, internet access, and API quota.
- **Static changes do not appear:** hard refresh the browser.

