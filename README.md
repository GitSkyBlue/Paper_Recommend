# 🤖 AI 논문 추천 챗봇
> SeSAC ChatGPT & LangChain을 활용한 LLM 기반 AI 앱 개발 미니프로젝트
<br>

## 📌 1. 프로젝트 소개

- 핵심 키워드를 자동으로 뽑아 논문을 검색 & 추천해주는 챗봇
- 유저의 요구사항에 따른 맞춤형 시스템

<br>

## 📌 2. 개발 기간 & 팀원 구성

- 개발 기간 : 2025-04-02 ~ 2025-04-07   

<div align="left">

| **지용욱** | **박제형** |
| :------: |  :------: |
| [<img src="https://avatars.githubusercontent.com/GitSkyBlue" height=150 width=150> <br/> @GitSkyBlue](https://github.com/GitSkyBlue) | [<img src="https://avatars.githubusercontent.com/PJH-02" height=150 width=150> <br/> @PJH-02](https://github.com/PJH-02) |

</div>

<br>

## 📌 3. 기술 스택

### Environment

<img src="https://img.shields.io/badge/Visual%20Studio%20Code-007ACC?style=for-the-badge&logo=Visual%20Studio%20Code&logoColor=white"><img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=GitHub&logoColor=white"><img src="https://img.shields.io/badge/Slack-4A154B?style=for-the-badge&logo=Slack&logoColor=white">

### Development   

<img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=Python&logoColor=white"><img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white"><img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=FastAPI&logoColor=white"><img src="https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=LangChain&logoColor=white"><img src="https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=OpenAI&logoColor=white"><img src="https://img.shields.io/badge/Hugging Face-FFD21E?style=for-the-badge&logo=Hugging Face&logoColor=white"><img src="https://img.shields.io/badge/Selenium-43B02A?style=for-the-badge&logo=Selenium&logoColor=white">

### Database

<img src="https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=MySQL&logoColor=white">

## 📌 4. 프로젝트 구조

📂 ai_paper_summary   
┣ 📂 backend   
┃ ┣ 📜 db.py   
┃ ┣ 📜 main.py   
┃ ┣ 📜 models.py   
┃ ┣ 📜 search.py   
┃ ┣ 📜 similarity.py   
┃ ┣ 📜 summary.py   
┣ 📂 frontend   
┃ ┣ 📜 app.py   
┃ 📜 .env   
┃ 📜 db.sql   
┃ 📜 requirements.txt   
┗ 📜 README.md   

## 📌 5. 실행 가이드

### Installation   
```
$ git clone https://github.com/GitSkyBlue/Paper_Recommend.git
$ cd Paper_Recommend
$ pip install -r requirements.txt
```

### Frontend   
```
$ streamlit run frontend/app.py
```

### Backend   
```
$ uvicorn backend.main:app --reload
```

### Database
```
$ db.sql
```