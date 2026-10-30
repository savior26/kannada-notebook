from pydantic import BaseModel, Field
from typing import Optional, List


class OCRWord(BaseModel):
    text: str
    confidence: float
    left: int
    top: int
    width: int
    height: int


class OCRPageResult(BaseModel):

    page_number: int
    raw_text: str
    confidence: float
    words: list
    preprocessing_method: str
    document_classification: str
    extraction_method: str


class OCRDocumentResult(BaseModel):

    filename: str
    document_type: str
    total_pages: int
    text: str
    average_confidence: float
    pages: List[OCRPageResult]
    document_classification: str