from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os
import fitz
import glob
from openai import OpenAI
import certifi

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

def DownloadPDF(paper_infos):
    download_dir = os.path.abspath("downloads")  # 현재 폴더 내 'downloads' 폴더에 저장

    # 🔧 Chrome 옵션 설정
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,  # 다운로드 경로 설정
        "download.prompt_for_download": False,  # 다운로드 창 비활성화
        "download.directory_upgrade": True,  # 기존 설정 유지
        "plugins.always_open_pdf_externally": True  # PDF 뷰어 대신 다운로드
    })

    # 🌐 Chrome 드라이버 실행
    driver = webdriver.Chrome(options=chrome_options)

    for data in paper_infos:
        pdf_url = data[2]
        paper_id = data[1]  # paperId 가져오기

        # 🚀 페이지 이동 (다운로드 자동 시작)
        driver.get(pdf_url)

        # ⏳ 다운로드 대기 (파일 다운로드 시간 확보)
        time.sleep(7)

        # 🔍 최신 다운로드된 파일 찾기
        downloaded_files = glob.glob(os.path.join(download_dir, "*.pdf"))  # downloads 폴더 내 PDF 파일 목록 가져오기
        if downloaded_files:
            latest_file = max(downloaded_files, key=os.path.getctime)  # 가장 최근에 생성된 파일 찾기
            new_file_path = os.path.join(download_dir, f"{paper_id}.pdf")  # 새 파일명 설정

            # 📝 파일명 변경
            os.rename(latest_file, new_file_path)
            print(f"📂 {latest_file} → {new_file_path} 로 변경 완료!")

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
            max_tokens=100,
            temperature=0.6,
        )

        print(file, '\n', response.choices[0].message.content)

if __name__ == '__main__':
    Summarize(OpenAI())
   