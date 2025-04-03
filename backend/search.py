from openai import OpenAI
from dotenv import load_dotenv
import requests
import time
import os
import certifi

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

def FindBySearchQuery(SearchQuery):
    ID_URL = f"https://api.semanticscholar.org/graph/v1/paper/search?query={search_Query}&fields=url,abstract&limit=5"

    headers = {"x-api-key": SEMANTIC_API_KEY}
    response = requests.get(ID_URL, headers=headers)

    return response.json()

if __name__ == '__main__':
    client = OpenAI()
    query = 'summarize ai related paper'
    search_Query, user_Request = KeywordAndTranslate(query, client)

    result = FindBySearchQuery(search_Query)
    print(result)