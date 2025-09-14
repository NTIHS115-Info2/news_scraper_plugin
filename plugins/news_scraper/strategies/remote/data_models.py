# plugins/news_scraper/strategies/remote/data_models.py
from pydantic import BaseModel, Field
from typing import List, Optional

# --- Scraper Models ---
class ScraperResult(BaseModel):
    source_url: str
    article_text: str

class ScraperOutput(BaseModel):
    success: bool
    result: Optional[ScraperResult] = None
    error: Optional[str] = None
    # [V10.0.1 歷史恢復] 恢復 errors 欄位以處理部分失敗
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
    resultType: str = "list"