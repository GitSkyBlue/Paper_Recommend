import streamlit as st
import time
import backend.search
from dotenv import load_dotenv
import certifi
import os
from openai import OpenAI
import backend.similarity
import backend.summary
import re

load_dotenv()

SEMANTIC_API_KEY = os.getenv('SEMANTIC_API_KEY')
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["SSL_CERT_FILE"] = certifi.where()

client = OpenAI()

# 🌟 Streamlit 페이지 설정
st.set_page_config(page_title="AI 논문 추천 챗봇", page_icon="📚", layout="centered")

# 🎨 CSS 적용 (채팅 입력 칸 정렬 + 크기 유지)
st.markdown("""
    <style>
        .chat-container {
            max-width: 700px;
            margin: auto;
        }
        .chat-message {
            padding: 12px;
            border-radius: 10px;
            margin: 5px 0;
            max-width: 80%;
        }
        .user {
            background-color: #007AFF;
            color: white;
            text-align: right;
            align-self: flex-end;
        }
        .bot {
            background-color: #E5E5EA;
            color: black;
            text-align: left;
            align-self: flex-start;
        }
    </style>
""", unsafe_allow_html=True)

# 🎯 세션 상태 초기화
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "step" not in st.session_state:
    st.session_state["step"] = -1  # -1: 논문 분야 선택, 0: 질문 입력, 1: 논문 추천, 2: 논문 선택
if "first_question" not in st.session_state:
    st.session_state["first_question"] = True  # 첫 번째 질문인지 여부
if "selected_field" not in st.session_state:
    st.session_state["selected_field"] = None
if "papers" not in st.session_state:
    st.session_state["papers"] = []
if "selected_paper" not in st.session_state:
    st.session_state["selected_paper"] = None

# 📌 채팅 메시지 출력 함수
def display_chat():
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for sender, message in st.session_state["chat_history"]:
        css_class = "user" if sender == "user" else "bot"
        st.markdown(f'<div class="chat-message {css_class}">{message}</div>', unsafe_allow_html=True)

# 🏁 챗봇 타이틀
st.title("🤖 AI 논문 추천 챗봇")

display_chat()

# 📌 -1. 논문 분야 선택 단계
if st.session_state["step"] == -1:
    st.subheader("📚 관심 있는 논문 분야를 선택하세요!")

    fields = [
        "Medicine", "Engineering", "Computer Science", "Environmental Science", 
        "Psychology", "Education", "Sociology", "Business", "Economics", "Political Science"
    ]
    
    selected_field = st.selectbox("논문 분야 선택:", fields)
    
    if st.button("선택 완료"):
        st.session_state["selected_field"] = selected_field
        st.session_state["chat_history"].append(("bot", f"✅ 선택한 분야: **{selected_field}**"))
        st.session_state["step"] = 0  # 질문 입력 단계로 이동
        st.rerun()

# 📌 0. 사용자 질문 입력 단계
if st.session_state["step"] == 0:
    if st.session_state["first_question"]:  # 첫 번째 질문이면 문구 표시
        st.subheader("💬 질문을 입력하세요:")
    
    user_input = st.chat_input("질문을 입력하세요.")  # 입력창 길이 통일

    if user_input: #이게 쿼리
        st.session_state["chat_history"].append(("user", user_input))
        st.session_state["step"] = 1  # 다음 단계로 진행
        st.session_state["first_question"] = False  # 첫 질문 이후로는 문구 숨김

        #백엔드 가동
        # 🛠 selected_field를 세션 상태에서 가져오기
        selected_field = st.session_state.get("selected_field")

        SearchQuery, user_request = backend.search.KeywordAndTranslate(user_input, client)
        json_Data = backend.search.FindBySearchQuery(SearchQuery, selected_field)
        st.session_state['SearchQuery'] = SearchQuery
        st.session_state['user_request'] = user_request
        st.session_state["json_Data"] = json_Data
        st.rerun()

# 📌 1. 논문 추천 단계
if st.session_state["step"] == 1:
    with st.spinner("🔎 논문을 검색하는 중..."):
        time.sleep(0.1)
        
    #데이터 정제
    json_Data = st.session_state.get("json_Data", None)
    results = backend.similarity.SetData(json_Data)

    #유사도 비교
    SearchQuery = st.session_state.get("SearchQuery", None)
    sim_list = backend.similarity.CheckSimilarity(SearchQuery, results)

    #제목+초록 가져오기
    paper_infos = backend.summary.FindIDAndURL(sim_list, json_Data, client)
    print('*'*100)
    print(paper_infos)
    print('*'*100)
    paper_infos = backend.summary.DownloadPDF(paper_infos)
    print(paper_infos)

    paper_list = "\n\n".join([f"📄 {i+1}. {title}\n\n-{translate}\n\n{url}" for i, (id, title, url, abstract, translate) in enumerate(paper_infos)])
    st.session_state["papers"] = paper_infos

    st.session_state["chat_history"].append(("bot", f"다음 논문들을 추천드립니다.\n\n{paper_list}\n\n🔽 분석할 논문을 선택해주세요!"))
    st.session_state["step"] = 2  # 논문 선택 단계로 이동
    st.rerun()

# 📌 2. 논문 선택 단계
elif st.session_state["step"] == 2:
    st.subheader("📑 분석할 논문을 선택하세요:")
    
    cols = st.columns(3)  # 논문 선택 버튼 3개를 가로로 배치
    for i, paper in enumerate(st.session_state["papers"]):
        with cols[i]:
            if st.button(f"논문 {i+1} 분석"):
                st.session_state["selected_paper"] = paper
                st.session_state["step"] = 3  # 논문 분석 단계로 이동
                st.rerun()

# 📌 3. 논문 분석 결과 출력 단계
if st.session_state["step"] == 3:
    selected_paper = st.session_state["selected_paper"]
    user_request = st.session_state['user_request']
    
    answer = backend.summary.Summarize(client, user_request)

    for title, summary in answer:
        selection = re.sub(r'[<>:"/\\|?*]', '', selected_paper[1])  # 파일명 정리
        if selection == title.replace('.pdf', ''):
            print('k'*100)
            print(title.replace('.pdf', ''))
            print(summary)
            print(selected_paper[1])
            st.session_state["chat_history"].append(("user", f"📄 선택한 논문: **{title}**"))
            st.session_state["chat_history"].append(("bot", f"📝 논문 주요 내용 요약: {summary}"))
            st.session_state["chat_history"].append(("bot", "✅ AI가 추천하는 연구 방향:\n- 이 논문의 방법론을 실제 데이터셋에 적용해보세요.\n- 최신 트렌드와 비교 분석하여 더 나은 모델을 찾아보세요."))
            st.session_state['title'] = title
            st.session_state["step"] = 4  # 다시 질문을 받도록 초기화
            st.rerun()

if st.session_state['step'] == 4:
    st.subheader("💬 추가 질문을 기다리는 중...")
    
    user_more_input = st.chat_input("추가 질문을 입력하세요.")

    if user_more_input:
        st.session_state["chat_history"].append(("user", user_more_input))
        
        # 의도 분류 (가정: backend.intent라는 모듈에 ClassifyIntent 함수 존재)
        intent = backend.search.ClassifyIntentGPT(client, user_more_input)
        
        if intent == "search":  # 검색 의도
            st.session_state["chat_history"].append(("bot", "🔎 새로운 논문 검색 요청으로 인식했습니다. 검색을 시작합니다..."))
            st.session_state["step"] = 1  # 논문 추천 단계로 이동
            st.session_state["first_question"] = False
            
            # 백엔드 검색 로직 재사용
            SearchQuery, user_request = backend.search.KeywordAndTranslate(user_more_input, client)
            json_Data = backend.search.FindBySearchQuery(SearchQuery, st.session_state["selected_field"])
            st.session_state["SearchQuery"] = SearchQuery
            st.session_state["user_request"] = user_request
            st.session_state["json_Data"] = json_Data
            st.rerun()
        
        elif intent == "more_analysis":  # 추가 분석 요구
            st.session_state["chat_history"].append(("bot", "📑 논문에 대한 추가 분석 요청으로 인식했습니다. 처리 중..."))
            title = st.session_state['title']

            #사용자 쿼리를 바탕으로 논문 pdf 읽어서 분석하고 출력하는 함수
            additional_summary = backend.summary.AdditionalAnalysis(client, user_more_input, title)
            st.session_state["chat_history"].append(("bot", f"📝 추가 분석 결과: {additional_summary}"))
            st.session_state["step"] = 4  # Step 4 유지 (추가 질문 대기)
            st.rerun()
