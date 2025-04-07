from pydantic import BaseModel
from typing import List, Optional, Dict, Literal
    
# Search
class QueryInput(BaseModel):
    query: str

class PaperSearchRequest(BaseModel):
    search_query: str
    selected_field: str

# Similarity
class PaperItem(BaseModel):
    paperId: str
    title: str
    abstract: Optional[str] = ""

class SimilarityRequest(BaseModel):
    search_query: str
    json_data: List[PaperItem]

# Summary
class SimText(BaseModel):
    page_content: str

class FindIDAndURLRequest(BaseModel):
    sim_list: List[SimText]
    json_data: List[Dict]

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

# DB
class ChatLog(BaseModel):
    session_id: str
    username: str
    role: Literal["user", "bot"]
    message: str
    search_query: str

class SummaryLog(BaseModel):
    title: str
    summary: str