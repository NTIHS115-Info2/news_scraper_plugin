# plugins/news_scraper/strategies/remote/models.py
from pydantic import BaseModel, Field
from typing import List, Optional

# --- Scraper Models ---
class ScraperResult(BaseModel):
    source_urls: List[str]
    article_text: str

class ScraperOutput(BaseModel):
    success: bool
    result: Optional[ScraperResult] = None
    errors: List[str] = Field(default_factory=list)
    resultType: str = "object"

# --- Librarian Models ---
class LibrarianInput(BaseModel):
    text_content: str
    query: str

class RelevantSection(BaseModel):
    chunk: str
    score: float

class LibrarianResult(BaseModel):
    relevant_sections: List[RelevantSection]

class LibrarianOutput(BaseModel):
    success: bool
    result: Optional[LibrarianResult] = None
    error: Optional[str] = None
    resultType: str = "object" # 根據 tool-description.json 應為 json

# --- Summarizer Models ---
class SummarizerInput(BaseModel):
    chunks: List[str]
    mode: str = "single"
    length: str = "medium"

class MultiAngleSummary(BaseModel):
    original_chunk: str
    summary: str

class SingleSummary(BaseModel):
    summary: str

class SummarizerResult(BaseModel):
    summary: Optional[str] = None
    multi_angle_summaries: Optional[List[MultiAngleSummary]] = None

class SummarizerOutput(BaseModel):
    success: bool
    result: Optional[SummarizerResult] = None
    error: Optional[str] = None
    resultType: str = "object"