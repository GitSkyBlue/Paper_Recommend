from openai import OpenAI
import certifi
from .models import FindIDAndURLRequest, DownloadPDFRequest, AdditionalAnalysisRequest, SummarizeRequest, SummarizeAbstractRequest
from fastapi import APIRouter
import os, re, shutil, glob, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import fitz  # PyMuPDF

os.environ["CURL_CA_BUNDLE"] = ""
os.environ["SSL_CERT_FILE"] = certifi.where()

router = APIRouter()
client = OpenAI()  # 환경변수 OPENAI_API_KEY 필요

def wait_for_downloads(download_dir, timeout=60):
    """ 다운로드가 완료될 때까지 대기 """
    start_time = time.time()
    while True:
        time.sleep(1)  # 1초마다 체크
        downloading_files = glob.glob(os.path.join(download_dir, "*.crdownload"))  # 아직 다운로드 중인 파일 확인
        if not downloading_files:  # 다운로드 중인 파일이 없으면 종료
            break
        if time.time() - start_time > timeout:  # 최대 대기 시간 초과 시 종료
            print("⚠ 다운로드 대기 시간 초과!")
            break

@router.post("/FindIDAndURL")
def find_id_and_url(request: FindIDAndURLRequest):
    sim_list = request.sim_list
    json_Data = request.json_data
    paper_info = []

    for sim_text in sim_list:
        title = sim_text.page_content.split('\n')[0]
        for data in json_Data:
            if data['title'] == title:
                paper_info.append([
                    data['paperId'],
                    data['title'],
                    data['openAccessPdf']['url'],
                    data.get('abstract', 'No abstract available')
                ])
                break

    return paper_info

@router.post("/DownloadPDF")
def download_pdf(request: DownloadPDFRequest):
    paper_infos = request.paper_infos
    download_dir = os.path.abspath("downloads")

    if os.path.exists(download_dir):
        shutil.rmtree(download_dir)
    os.makedirs(download_dir, exist_ok=True)

    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    })

    driver = webdriver.Chrome(options=chrome_options)
    successful_papers = []

    for data in paper_infos:
        pdf_url = data.pdf_url
        paper_id = re.sub(r'[<>:"/\\|?*]', '', data.title)

        before_files = set(glob.glob(os.path.join(download_dir, "*.pdf")))
        driver.get(pdf_url)
        wait_for_downloads(download_dir)
        time.sleep(2)

        after_files = set(glob.glob(os.path.join(download_dir, "*.pdf")))
        new_files = list(after_files - before_files)

        if not new_files:
            print(f"⚠ {paper_id}.pdf 파일을 찾을 수 없음!")
            continue

        latest_file = max(new_files, key=os.path.getctime)
        new_file_path = os.path.join(download_dir, f"{paper_id}.pdf")

        try:
            if latest_file != new_file_path:
                os.rename(latest_file, new_file_path)
                print(f"📂 {latest_file} → {new_file_path} 로 변경 완료!")
            else:
                print(f"✅ {new_file_path} 이름 변경 불필요")

            successful_papers.append(data)
        except Exception as e:
            print(f'{paper_id}.pdf 이름 변경 실패: {e}')

        if len(successful_papers) == 3:
            break

    driver.quit()
    print(f"✅ PDF 다운로드 완료: {download_dir}")
    return [paper.dict() for paper in successful_papers]

@router.post("/SummarizeAbstract")
def summarize_abstract_papers(request: SummarizeAbstractRequest):
    results = []
    for i, paper in enumerate(request.sum_list):
        response = client.chat.completions.create(
            messages=[
                {'role': 'system', 'content': '''
                    You are an AI assistant that summarizes and translates research abstracts concisely and accurately.  
                    Follow these steps:  
                    1. Summarize the abstract in **three sentences**:  
                    - The research problem and significance.  
                    - The main approach/methodology.  
                    - The key findings and implications.  
                    2. Translate the summary into Korean. 
                    3. From your answer, only give translated answer. Do not give English summary of the abstract.
                '''},
                {'role': 'user', 'content': paper.abstract}
            ],
            model='gpt-4o-mini',
            max_tokens=1024,
            temperature=0.6,
        )
        results.append({'title': paper.title, 'abstract': response.choices[0].message.content})

    return results

@router.post("/Summarize")
def summarize_papers(request: SummarizeRequest):
    path = 'downloads/'
    file_path = os.path.join(path, re.sub(r'[<>:"/\\|?*]', '', request.selected_paper)+'.pdf')

    # 파일 존재 확인
    if not os.path.exists(file_path):
        return {"error": f"📁 파일이 존재하지 않습니다: {request.selected_paper}"}

    # PDF 열기
    doc = fitz.open(file_path)
    text = "\n".join([page.get_text("text") for page in doc])

    system_prompt = f'''
    You are an AI research assistant that processes academic papers based on specific user requests.  
    Your primary task is to analyze the given research paper and provide an accurate response according to the user's request.  

    📌 **Instructions:**  
    1️. **Understand the user's request `{request.user_request}`.**  
    2️. **Extract and provide ONLY the requested information.**  
    3. Consider everything between "Introduction" and "Conclusion" as the main content.
    4. Summarize the **Introduction** - briefly state the background and the research question.
    5. Summarize the **Main Content** - focus on methodology, experiments, and key findings in a concise but informative way.
    6. Summarize the **Conclusion** - highlight the achievements and possible future directions.
    7. Format the response with clear headings for each section.
    8. 반드시 한국어로 답변하세요.
    9. 번역되기 전 원문을 절대로 답변하지마세요.
    '''

    # GPT 호출
    response = client.chat.completions.create(
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': text}
        ],
        model='gpt-4o-mini',
        max_tokens=1024,
        temperature=0.4,
    )

    return {"title": request.selected_paper, "summary": response.choices[0].message.content}

@router.post("/AdditionalAnalysis")
def additional_analysis(request: AdditionalAnalysisRequest):
    doc = fitz.open('./downloads/' + re.sub(r'[<>:"/\\|?*]', '', request.title)+'.pdf')
    text = "\n".join([page.get_text("text") for page in doc])
    
    response = client.chat.completions.create(
        messages=[
                {'role': 'system', 'content': f"""
                You are an AI research assistant that processes academic papers based on specific user requests.  
                Your primary task is to analyze the given research paper and provide an accurate response according to the user's request.  
                Based on {text}, generate best answer about user's input.
                반드시 한국어로 답변하세요.
                """},
                {'role': 'user', 'content': request.user_more_input}
            ],
            model='gpt-4o-mini',
            max_tokens=1024,
            temperature=0.6,
    )

    return response.choices[0].message.content

if __name__ == '__main__':
    pass