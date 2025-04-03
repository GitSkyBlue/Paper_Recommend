from openai import OpenAI
from dotenv import load_dotenv
import requests
import time
import os
import certifi
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

SEMANTIC_API_KEY = os.getenv('SEMANTIC_API_KEY')
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["SSL_CERT_FILE"] = certifi.where()

def KeywordAndTranslate(query, client):
    response = client.chat.completions.create(
        messages=[
            {'role': 'system', 'content': '''
        You are an AI assistant that helps process academic research queries.
        Analyze the user's question and extract:
        1. **Search Query**: Extract the **exact research topic or paper title**. DO NOT generate a new topic. If the user provides a paper title, return it exactly as given.
        2. **User Request**: Identify any additional actions (e.g., summarizing, extracting equations, listing references).
        3. never use korean
            '''},
            {'role': 'user', 'content': query}
        ],
        model='gpt-4o-mini',
        max_tokens=1024,
        temperature=0.6,
    )

    print(response.choices[0].message.content)

    search_Query = response.choices[0].message.content.split('Search Query**: ')[-1].split('\n')[0].strip()
    user_Request = response.choices[0].message.content.split('Search Query**: ')[-1].split('User Request**: ')[-1]

    print('Search Query :', search_Query)
    print('User Request :', user_Request)

    return search_Query, user_Request

def get_pdf_link_selenium(paper_url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get(paper_url)
        time.sleep(5)  # 페이지 로드 대기
        
        # PDF 버튼 찾기
        pdf_buttons = driver.find_elements(By.CSS_SELECTOR, "a[data-test-id='paper-link']")
        for button in pdf_buttons:
            href = button.get_attribute("href")
            if href and href.endswith(".pdf"):
                return href
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None
    finally:
        driver.quit()

def FindBySearchQuery(SearchQuery):
    ID_URL = f"https://api.semanticscholar.org/graph/v1/paper/search?query={SearchQuery}&fields=url,abstract&limit=10"

    headers = {"x-api-key": SEMANTIC_API_KEY}
    response = requests.get(ID_URL, headers=headers)
    data = response.json()
    
    end = []
    papers = data.get('data', [])
    for paper in papers:
        open_access_pdf = paper.get('openAccessPdf')
        if not open_access_pdf['url']:
            pass
            # paper_url = paper.get('url')
            # pdf_link = get_pdf_link_selenium(paper_url)
            # if not pdf_link:
            #     #권한 문제 있는 논문이라고 url과 함께 저장하면 됨
            #     pass
        else:
            end.append(paper)
    return end

if __name__ == '__main__':
    client = OpenAI()
    query = 'summarize ai related paper'
    search_Query, user_Request = KeywordAndTranslate(query, client)

    result = FindBySearchQuery(search_Query)
    print(result)