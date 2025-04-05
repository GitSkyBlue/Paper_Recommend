from pydantic import BaseModel
from typing import List, Optional, Dict, Literal
    
class QueryInput(BaseModel):
    query: str

class PaperSearchRequest(BaseModel):
    search_query: str
    selected_field: str

class PaperItem(BaseModel):
    paperId: str
    title: str
    abstract: Optional[str] = ""

class SimilarityRequest(BaseModel):
    search_query: str
    json_data: List[PaperItem]

class SimText(BaseModel):
    page_content: str

class FindIDAndURLRequest(BaseModel):
    sim_list: List[SimText]
    json_data: List[Dict]

# 📦 요청 데이터 구조 정의
class PaperInfo(BaseModel):
    paper_id: str
    title: str
    pdf_url: str
    abstract: str
    summary: str

class DownloadPDFRequest(BaseModel):
    paper_infos: List[PaperInfo]

class SummarizeRequest(BaseModel):
    user_request: str
    selected_paper: str

class AdditionalAnalysisRequest(BaseModel):
    user_more_input: str
    title: str

class ChatLog(BaseModel):
    session_id: str
    role: Literal["user", "bot"]
    message: str

class SummaryLog(BaseModel):
    title: str
    summary: str

class CheckRequest(BaseModel):
    title: str