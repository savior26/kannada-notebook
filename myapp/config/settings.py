import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Settings(BaseModel):
    DATABASE_URL: str
    SECRET_KEY: str = Field(min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, gt=0)
    COOKIE_SECURE: bool = True
    TESSERACT_CMD: str = "tesseract"
    OCR_LANGUAGE: str = "kan"
    OCR_ENGINE_MODE: int = 1
    OCR_PAGE_SEGMENTATION: int = 6

    @property
    def EXPIRY(self) -> int:
        """Compatibility alias; expiry is expressed in minutes."""
        return self.ACCESS_TOKEN_EXPIRE_MINUTES


database_url = os.getenv("DATABASE_URL")
secret_key = os.getenv("SECRET_KEY")
if not database_url:
    raise ValueError("DATABASE_URL environment variable is not set")
if not secret_key:
    raise ValueError("SECRET_KEY environment variable is not set (use a random value of at least 32 characters)")

settings = Settings(
    DATABASE_URL=database_url,
    SECRET_KEY=secret_key,
    ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
    ALGORITHM=os.getenv("JWT_ALGORITHM", "HS256"),
    COOKIE_SECURE=os.getenv("COOKIE_SECURE").lower() == "true",
    TESSERACT_CMD=os.getenv("TESSERACT_CMD", "tesseract"),
    OCR_LANGUAGE=os.getenv("OCR_LANGUAGE", "kan"),
    OCR_ENGINE_MODE=int(os.getenv("OCR_ENGINE_MODE", "1")),
    OCR_PAGE_SEGMENTATION=int(os.getenv("OCR_PAGE_SEGMENTATION", "6")),
)
