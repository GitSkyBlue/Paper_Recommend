from openai import OpenAI
from dotenv import load_dotenv
import requests
import os
import certifi
from fastapi import APIRouter
from openai import OpenAI
from .models import QueryInput, PaperSearchRequest

load_dotenv()

SEMANTIC_API_KEY = os.getenv('SEMANTIC_API_KEY')
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["SSL_CERT_FILE"] = certifi.where()

router = APIRouter()
client = OpenAI()

@router.post("/QueryAndRequest")
def get_query_and_request(request: QueryInput):
    response = client.chat.completions.create(
        messages=[
            {'role': 'system', 'content': '''
            You are an AI assistant that helps process academic research queries.
            Analyze the user's question and extract:
            1. If user's query is written in Korean, translate it into English.
            2. **Search Query**: Extract the **exact research topic or paper title**. DO NOT generate a new topic. If the user provides a paper title, return it exactly as given.
            3. **User Request**: Identify any additional actions (e.g., summarizing, extracting equations, listing references).
            3. Never use Korean.
            '''},
            {'role': 'user', 'content': request.query}
        ],
        model='gpt-4o-mini',
        max_tokens=128,
        temperature=0.1,
    )

    result = response.choices[0].message.content

    # 파싱
    search_Query = result.split('Search Query**: ')[-1].split('\n')[0].strip().replace('"', '')
    user_Request = result.split('User Request**: ')[-1].strip()

    return search_Query, user_Request

@router.post("/FindBySearchQuery")
def find_by_search_query(request: PaperSearchRequest):
    search_query = request.search_query
    selected_field = request.selected_field

    ID_URL = f"https://api.semanticscholar.org/graph/v1/paper/search?query={search_query}&fields=url,abstract,fieldsOfStudy,openAccessPdf&limit=50"
    headers = {"x-api-key": SEMANTIC_API_KEY}
    
    response = requests.get(ID_URL, headers=headers)
    data = response.json()

    end = []
    papers = data.get('data', [])

    for paper in papers:
        category = paper.get('fieldsOfStudy')
        open_access_pdf = paper.get('openAccessPdf') or {}
        pdf_url = open_access_pdf.get('url')

        if pdf_url:
            if isinstance(category, list):
                if selected_field in category:
                    end.append(paper)
            elif category == selected_field:
                end.append(paper)

    return end

if __name__ == '__main__':
    pass