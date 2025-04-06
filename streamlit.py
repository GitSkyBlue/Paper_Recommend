import streamlit as st
import time
from dotenv import load_dotenv
import certifi
import os
from openai import OpenAI
import requests
import uuid

username = 'sky'
    
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
        /* 사이드바 버튼 스타일 */
        section[data-testid="stSidebar"] button {
            background-color: #f0f0f5;
            color: #333;
            border: none;
            border-radius: 6px;
            padding: 0.6em 1em;
            font-weight: 500;
            transition: background-color 0.3s, color 0.3s;
        }

        /* 마우스 오버 효과 */
        section[data-testid="stSidebar"] button:hover {
            background-color: #e4e4ec;
            color: #000;
            cursor: pointer;
        }
    </style>
""", unsafe_allow_html=True)

## loading
if "initializing" not in st.session_state:
    st.session_state["initializing"] = True

if st.session_state["initializing"]:
    with st.spinner("로딩 중입니다..."):
        # 초기화 로직 (예: 세션 상태 설정, 서버 요청 등)
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []
        if "step" not in st.session_state:
            st.session_state["step"] = -1
        if "first_question" not in st.session_state:
            st.session_state["first_question"] = True
        if "selected_field" not in st.session_state:
            st.session_state["selected_field"] = None
        if "papers" not in st.session_state:
            st.session_state["papers"] = []
        if "selected_paper" not in st.session_state:
            st.session_state["selected_paper"] = None
        if "history_mode" not in st.session_state:
            st.session_state["history_mode"] = False
        if "selected_history_session" not in st.session_state:
            st.session_state["selected_history_session"] = None

        # 세션 목록도 처음 로딩
        if "available_sessions" not in st.session_state:
            response = requests.get(f"http://localhost:8000/ChatHistoryByUser/{username}")
            session_data = response.json().get("sessions", {})
            st.session_state["available_sessions"] = list(session_data.keys())
            st.session_state["session_data_dict"] = session_data

        # 이제 초기화 완료!
        st.session_state["initializing"] = False
        st.rerun()

# 📌 채팅 메시지 출력 함수
def display_chat():
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for sender, message in st.session_state["chat_history"]:
        css_class = "user" if sender == "user" else "bot"
        st.markdown(f'<div class="chat-message {css_class}">{message}</div>', unsafe_allow_html=True)

# 🏁 챗봇 타이틀
st.title("🤖 AI 논문 추천 챗봇")

# 기본 채팅 출력 (히스토리 모드 아닐 때만!)
if not st.session_state.get("history_mode", False):
    display_chat()

# 🧾 사이드바
with st.sidebar:
    st.header(f"👤 Username : {username}")
    st.header("📌 Menu")
    # 🏠 처음으로 돌아가기 버튼
    if st.button("🏠 Home"):
        # 리다이렉트 스크립트 삽입
        st.markdown("""
            <meta http-equiv="refresh" content="0; url=http://localhost:8501">
            <script>
                window.location.href = "http://localhost:8501";
            </script>
        """, unsafe_allow_html=True)
    if st.button("🧾 Contact Us"):
        pass

    st.header("💬 Library")

    # 세션 버튼들
    if st.session_state["available_sessions"]:
        for session_id in st.session_state["available_sessions"]:
            messages = st.session_state["session_data_dict"].get(session_id, [])
            first_user_msg = next((m["message"] for m in messages if m["role"] == "user"), "💬 (내용 없음)")
            preview = (first_user_msg[:17] + "...") if len(first_user_msg) > 17 else first_user_msg
            label = f"💬 {preview}"

            # 열을 나눠서 왼쪽은 세션 버튼, 오른쪽은 삭제 버튼
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                if st.button(label, key=f"session_{session_id}"):
                    st.session_state["history_mode"] = True
                    st.session_state["selected_history_session"] = session_id
                    st.rerun()

            with col2:
                if st.button("❌", key=f"delete_{session_id}"):
                    # 삭제 API 요청
                    delete_url = f"http://localhost:8000/DeleteChatSession"
                    response = requests.delete(delete_url, params={"username": username, "session_id": session_id})
                    if response.status_code == 200:
                        # 상태에서 해당 세션 제거
                        st.session_state["available_sessions"].remove(session_id)
                        st.session_state["session_data_dict"].pop(session_id, None)
                        st.success(f"세션 {session_id} 삭제됨")
                        st.rerun()
                    else:
                        st.error("세션 삭제 실패")

# 📜 선택된 세션의 히스토리 표시
if st.session_state.get("history_mode", False) and st.session_state.get("selected_history_session"):
    session_id = st.session_state["selected_history_session"]
    chat_history = requests.get(
        "http://localhost:8000/GetChatHistoryBySession",
        params={"username": username, "session_id": session_id}
    ).json()

    # st.subheader(f"📝 세션 {session_id}의 채팅 히스토리")
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    for chat in chat_history:
        role = chat["role"]
        message = chat["message"]
        css_class = "user" if role == "user" else "bot"
        st.markdown(f'<div class="chat-message {css_class}">{message}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# 📌 -1. 논문 분야 선택 단계
if st.session_state["step"] == -1 and not st.session_state.get("history_mode", False):
    st.session_state["session_id"] = str(uuid.uuid4())
    st.subheader("📚 관심 있는 논문 분야를 선택하세요!")

    fields = [
        "Medicine", "Engineering", "Computer Science", "Environmental Science", 
        "Psychology", "Education", "Sociology", "Business", "Economics", "Political Science"
    ]
    
    selected_field = st.selectbox("논문 분야 선택:", fields)
    
    if st.button("선택 완료"):
        st.session_state["selected_field"] = selected_field
        message = f"✅ 선택한 분야 : {selected_field}"
        requests.post("http://localhost:8000/SaveChat", json={"session_id": st.session_state["session_id"], "username": username, "role": "bot", "message": message})
        st.session_state["chat_history"].append(("bot", message))
        st.session_state["step"] = 0  # 질문 입력 단계로 이동
        st.rerun()

# 📌 0. 사용자 질문 입력 단계
if st.session_state["step"] == 0:
    if st.session_state["first_question"]:  # 첫 번째 질문이면 문구 표시
        st.subheader("💬 질문을 입력하세요:")
    
    user_input = st.chat_input("질문을 입력하세요.")  # 입력창 길이 통일

    if user_input: #이게 쿼리
        requests.post("http://localhost:8000/SaveChat", json={"session_id": st.session_state["session_id"], "username": username, "role": "user", "message": user_input})
        st.session_state["chat_history"].append(("user", user_input))
        st.session_state["step"] = 1  # 다음 단계로 진행
        st.session_state["first_question"] = False  # 첫 질문 이후로는 문구 숨김

        #백엔드 가동
        # 🛠 selected_field를 세션 상태에서 가져오기
        selected_field = st.session_state.get("selected_field")

        search_Query, user_Request = requests.post("http://localhost:8000/QueryAndRequest", json={"query": user_input}).json()
        
        json_Data = requests.post("http://localhost:8000/FindBySearchQuery", json={"search_query": search_Query, "selected_field": selected_field}).json()
        
        st.session_state['SearchQuery'] = search_Query
        st.session_state['user_request'] = user_Request
        st.session_state["json_Data"] = json_Data
        st.rerun()

# 📌 1. 논문 추천 단계
if st.session_state["step"] == 1:
    with st.spinner("🔎 논문을 검색하는 중..."):
        time.sleep(0.1)
        
    #데이터 정제
    json_Data = st.session_state.get("json_Data", None)
    results = []

    for data in json_Data:
        temp = {}
        temp['paperId'] = data['paperId']
        temp['title'] = data['title']
        temp['abstract'] = data['abstract']

        results.append(temp)

    #유사도 비교
    search_Query = st.session_state.get("SearchQuery", None)
    sim_list = requests.post("http://localhost:8000/CheckSimilarity", json={'search_query': search_Query, 'json_data': results}).json()

    #제목+초록 가져오기
    paper_infos = requests.post("http://localhost:8000/FindIDAndURL", json={"sim_list": [{"page_content": doc["page_content"]} for doc in sim_list], "json_data": json_Data}).json()
    
    # 변환
    formatted_papers = [
        {
            "paper_id": item[0],
            "title": item[1],
            "pdf_url": item[2],
            "abstract": item[3],
            "summary": item[4]
        }
        for item in paper_infos
    ]

    selected_paper_infos = requests.post("http://localhost:8000/DownloadPDF", json={'paper_infos': formatted_papers}).json()
    
    paper_list = "\n\n".join([f"📄 {i+1}. {paper_info['title']}\n\n-{paper_info['summary']}\n\n{paper_info['pdf_url']}" for i, paper_info in enumerate(selected_paper_infos)])
    st.session_state["papers"] = selected_paper_infos

    message = f"다음 논문들을 추천드립니다.\n\n{paper_list}\n\n🔽 분석할 논문을 선택해주세요!"
    requests.post("http://localhost:8000/SaveChat", json={"session_id": st.session_state["session_id"], "username": username, "role": "bot", "message": message})
    st.session_state["chat_history"].append(("bot", message))
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
    user_Request = st.session_state['user_request']
    
    answer = requests.post("http://localhost:8000/CheckExist", json={'title': selected_paper['title']}).json()
    if answer == 0:
        answer = requests.post("http://localhost:8000/Summarize", json={'user_request': user_Request, 'selected_paper': selected_paper['title']}).json()
    
    if answer:
        message = f"📄 선택한 논문: {answer['title']}"
        requests.post("http://localhost:8000/SaveChat", json={"session_id": st.session_state["session_id"], "username": username, "role": "user", "message": message})
        st.session_state["chat_history"].append(("user", message))

        message = f"📝 논문 주요 내용 요약: {answer['summary']}"
        requests.post("http://localhost:8000/SaveChat", json={"session_id": st.session_state["session_id"], "username": username, "role": "bot", "message": message})
        requests.post("http://localhost:8000/SaveSummary", json={"title": answer['title'], "summary": answer['summary']})
        st.session_state["chat_history"].append(("bot", message))

        st.session_state['title'] = answer['title']
        st.session_state["step"] = 4  # 다시 질문을 받도록 초기화
        st.rerun()

if st.session_state['step'] == 4:
    st.subheader("💬 추가 질문을 기다리는 중...")
    
    user_more_input = st.chat_input("추가 질문을 입력하세요.")

    if user_more_input:
        requests.post("http://localhost:8000/SaveChat", json={"session_id": st.session_state["session_id"], "username": username, "role": "user", "message": user_more_input})
        st.session_state["chat_history"].append(("user", user_more_input))
        
        title = st.session_state['title']
        
        additional_summary = requests.post("http://localhost:8000/AdditionalAnalysis", json={'user_more_input': user_more_input, 'title': title}).json()
        
        requests.post("http://localhost:8000/SaveChat", json={"session_id": st.session_state["session_id"], "username": username, "role": "bot", "message": f"📝 {additional_summary}"})
        st.session_state["chat_history"].append(("bot", f"📝 {additional_summary}"))
        st.session_state["step"] = 4  # Step 4 유지 (추가 질문 대기)
        st.rerun()
