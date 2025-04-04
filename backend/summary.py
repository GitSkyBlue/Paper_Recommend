from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os
import fitz
import glob
from openai import OpenAI
import certifi
import re

os.environ["CURL_CA_BUNDLE"] = ""
os.environ["SSL_CERT_FILE"] = certifi.where()

def FindIDAndURL(sim_list, json_Data):
    paper_info = []
    print(sim_list)
    for sim_text in sim_list:
        print(sim_text)
        title = sim_text.page_content.split('\n')[0]  # sim_list에서 제목 추출

        for data in json_Data:
            if data['title'] == title:  # 제목이 일치하는 경우에만 추가
                paper_info.append([data['paperId'], data['title'], data['openAccessPdf']['url'], data.get('abstract', 'No abstract available')])
                break  # 일치하는 논문을 찾았으면 더 이상 탐색할 필요 없음

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
    os.makedirs(download_dir, exist_ok=True)  # ✅ 폴더 없으면 생성

    # 🔧 Chrome 옵션 설정
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    })

    # 🌐 Chrome 드라이버 실행
    driver = webdriver.Chrome(options=chrome_options)

    for data in paper_infos:
        pdf_url = data[2]
        paper_id = re.sub(r'[<>:"/\\|?*]', '', data[1])  # 파일명 정리

        # 🚀 페이지 이동 (다운로드 자동 시작)
        driver.get(pdf_url)

        # ⏳ 다운로드 완료 대기
        wait_for_downloads(download_dir)

        # 🔍 최신 다운로드된 파일 찾기 (다시 검색)
        time.sleep(2)  # 추가 대기 (파일 시스템 처리 시간 확보)
        downloaded_files = glob.glob(os.path.join(download_dir, "*.pdf"))
        if not downloaded_files:
            print(f"⚠ {paper_id}.pdf 파일을 찾을 수 없음!")
            continue  # 다음 파일로 이동

        latest_file = max(downloaded_files, key=os.path.getctime)
        new_file_path = os.path.join(download_dir, f"{paper_id}.pdf")  # 새 파일명 설정

        # 📝 파일명 변경 (이미 존재하는 경우 덮어쓰기 방지)
        if latest_file != new_file_path:
            os.rename(latest_file, new_file_path)
            print(f"📂 {latest_file} → {new_file_path} 로 변경 완료!")
        else:
            print(f"✅ {new_file_path} 이름 변경 불필요 (이미 올바른 이름)")

    # 🚪 드라이버 종료
    driver.quit()
    print(f"✅ PDF 다운로드 완료: {download_dir}")

def Summarize(client):
    path = 'downloads/'
    file_list = os.listdir(path=path)

    for file in file_list:
        doc = fitz.open('./downloads/' + file)
        text = "\n".join([page.get_text("text") for page in doc])

        response = client.chat.completions.create(
            messages=[
                {'role': 'system', 'content': '''
                1. Every contents between introduciton and conclusion is considered as 'main contents'.
                2. Summarize the research paper's introduction
                3. Summarize the research paper's main contents in a concise and informative way.
                4. Summarize the research paper's conclusion. Focus on the research's achievements and future work.
                '''},
                {'role': 'user', 'content': text}
            ],
            model='gpt-4o-mini',
            max_tokens=1024,
            temperature=0.6,
        )

        print('FileName :', file)
        print('='*90)
        print(file, '\n', response.choices[0].message.content)

if __name__ == '__main__':
    Summarize(OpenAI())