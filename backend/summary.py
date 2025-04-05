from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os
import fitz
import glob
from openai import OpenAI
import certifi
import re
import shutil

os.environ["CURL_CA_BUNDLE"] = ""
os.environ["SSL_CERT_FILE"] = certifi.where()

def FindIDAndURL(sim_list, json_Data, client):
    paper_info = []
    print(sim_list)
    for sim_text in sim_list:
        print(sim_text)
        title = sim_text.page_content.split('\n')[0]  # sim_list에서 제목 추출

        for data in json_Data:
            if data['title'] == title:  # 제목이 일치하는 경우에만 추가
                paper_info.append([data['paperId'], data['title'], data['openAccessPdf']['url'], data.get('abstract', 'No abstract available')])
                break  # 일치하는 논문을 찾았으면 더 이상 탐색할 필요 없음

    for i, (id, title, pdf, abstract) in enumerate(paper_info):
        response = client.chat.completions.create(
                    messages=[
                        {'role': 'system', 'content': '''
                        You are an AI assistant that summarizes and translates research abstracts concisely and accurately.  \
                        Follow these steps:  
                        1. Summarize the abstract in **three sentences**:  
                        - The research problem and significance.  
                        - The main approach/methodology.  
                        - The key findings and implications.  
                        2. Translate the summary into Korean. 
                        3. From your answer, only give translated answer. Do not give English summary of the abstract.
                        '''},
                        {'role': 'user', 'content': abstract}
                    ],
                    model='gpt-4o-mini',
                    max_tokens=1024,
                    temperature=0.6,
                )
        paper_info[i].append(response.choices[0].message.content)
    return paper_info

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

def DownloadPDF(paper_infos):
    download_dir = os.path.abspath("downloads")  # 현재 폴더 내 'downloads' 폴더에 저장

    if os.path.exists(download_dir): #이전에 다운로드 받은 파일/폴더 있으면 자동 삭제제
        shutil.rmtree(download_dir)

    os.makedirs(download_dir, exist_ok=True)  # ✅ 폴더 없으면 생성

    # 🔧 Chrome 옵션 설정
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    })

    #Chrome 드라이버 실행
    driver = webdriver.Chrome(options=chrome_options)

    successful_papers = []

    for i, data in enumerate(paper_infos):
        pdf_url = data[2]
        paper_id = re.sub(r'[<>:"/\\|?*]', '', data[1])  # 파일명 정리

        #다운로드 전 파일 목록 기록
        before_files = set(glob.glob(os.path.join(download_dir, "*.pdf")))

        #페이지 이동 (다운로드 자동 시작)
        driver.get(pdf_url)

        #다운로드 완료 대기
        wait_for_downloads(download_dir)
        time.sleep(2)  # 추가 대기 (파일 시스템 처리 시간 확보)

        #다운로드 후 파일 목록 확인
        after_files = set(glob.glob(os.path.join(download_dir, "*.pdf")))
        new_files = list(after_files - before_files)

        #최신 다운로드된 파일 찾기 (다시 검색)
        if not new_files:
            print(f"⚠ {paper_id}.pdf 파일을 찾을 수 없음!")
            continue  # 다음 파일로 이동

        latest_file = max(new_files, key=os.path.getctime)
        new_file_path = os.path.join(download_dir, f"{paper_id}.pdf")  # 새 파일명 설정

        # 📝 파일명 변경 (이미 존재하는 경우 덮어쓰기 방지)
        try:
            if latest_file != new_file_path:
                os.rename(latest_file, new_file_path)
                print(f"📂 {latest_file} → {new_file_path} 로 변경 완료!")
            else:
                print(f"✅ {new_file_path} 이름 변경 불필요 (이미 올바른 이름)")

            successful_papers.append(data)  # ✅ 성공한 논문만 저장
        except Exception as e:
            print(f'{paper_id}.pdf 이름 변경 실패: {e}')

        # 🚪 드라이버 종료
        if len(successful_papers) == 3:
            driver.quit()
            print(f"✅ PDF 다운로드 완료: {download_dir}")
            return successful_papers
    return successful_papers

def Summarize(client, user_request):
    path = 'downloads/'
    file_list = os.listdir(path=path)

    final = []

    for file in file_list:
        doc = fitz.open('./downloads/' + file)
        text = "\n".join([page.get_text("text") for page in doc])

        if "summary" in user_request.lower() or "summariz" in user_request.lower():
            system_prompt = '''
            You are an AI research assistant that summarizes academic papers into well-structured Korean summaries.

            📌 Instructions:
            1. Consider everything between "Introduction" and "Conclusion" as the main content.
            2. Summarize the **Introduction** - briefly state the background and the research question.
            3. Summarize the **Main Content** - focus on methodology, experiments, and key findings in a concise but informative way.
            4. Summarize the **Conclusion** - highlight the achievements and possible future directions.
            5. Format the response with clear headings for each section.
            6. Translate the final response into fluent Korean.
            '''
        else:
            system_prompt = f'''
            You are an AI research assistant that processes academic papers based on specific user requests.  
            Your primary task is to analyze the given research paper and provide an accurate response according to the user's request.  
            The final response should be translated into Korean before being presented to the user.  

            📌 **Instructions:**  
            1️. **Understand the user's request `{user_request}`.**  
            - Identify whether the user wants a summary, formula extraction, reference list, methodology analysis, experimental results, dataset details, or another specific request.  
            - If the request is unclear, summarize the key aspects of the paper and prompt the user for further clarification.  
            - If the request is highly unusual, break it down logically and extract the most relevant information.  

            2️. **Extract and provide ONLY the requested information.**  
            - Summarize the paper **only if explicitly requested.**  
            - Extract mathematical formulas **only when needed.**  
            - List references **only when required.**  
            - Explain methodologies **only if the user asks.**  
            - Extract and analyze experimental results **only upon request.**  
            - Identify datasets **only if explicitly asked.**  
            - If the request does not match any of the above, infer the most relevant sections logically.  

            3️. **Translate the final response into Korean.**  
            - Ensure the original response is well-structured and clear.  
            - Translate the response into fluent and natural Korean before presenting it to the user.  
            - If multiple aspects are requested, separate each section accordingly.
            '''
        response = client.chat.completions.create(
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': text}
            ],
            model='gpt-4o-mini',
            max_tokens=1024,
            temperature=0.6,
        )

        print('FileName :', file)
        print('='*90)
        print(file, '\n', response.choices[0].message.content)
        final.append([file, response.choices[0].message.content])
    
    return final

def AdditionalAnalysis(client, user_more_input, title):
    doc = fitz.open('./downloads/' + title)
    text = "\n".join([page.get_text("text") for page in doc])
    
    response = client.chat.completions.create(
        messages=[
                {'role': 'system', 'content': f"""
                You are an AI research assistant that processes academic papers based on specific user requests.  
                Your primary task is to analyze the given research paper and provide an accurate response according to the user's request.  
                The final response should be translated into Korean before being presented to the user.
                Based on {text}, generate best answer about user's input.
                """},
                {'role': 'user', 'content': user_more_input}
            ],
            model='gpt-4o-mini',
            max_tokens=1024,
            temperature=0.6,
    )

    return response.choices[0].message.content

if __name__ == '__main__':
    Summarize(OpenAI())