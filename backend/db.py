from fastapi import APIRouter
import pymysql.cursors
from .models import ChatLog, SummaryLog, CheckRequest
import pymysql
from fastapi.responses import JSONResponse
from datetime import datetime

router = APIRouter()
def connect_to_mysql():
    return pymysql.connect(
        host='localhost',
        port=3308,
        user='root',
        passwd='1234',
        db='paper',
        charset='utf8mb4'
    )

@router.post("/SaveChat")
def save_chat(log: ChatLog):
    conn = connect_to_mysql()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_history (session_id, username, role, message) VALUES (%s, %s, %s, %s)",
        (log.session_id, log.username, log.role, log.message)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success"}

@router.post("/SaveSummary")
def save_summary(request: SummaryLog):
    conn = connect_to_mysql()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO summary_store (title, message) VALUES (%s, %s)",
        (request.title, request.summary)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return {'status': 'success'}

@router.post("/CheckExist")
def check_exist(request: CheckRequest):
    conn = connect_to_mysql()
    cursor = conn.cursor()
    title = request.title
    sql = f'SELECT message FROM summary_store WHERE title="{title}";'
    cursor.execute(sql)

    results = cursor.fetchone()  # 결과 모두 가져오기
    
    cursor.close()
    conn.close()

    if results == None:
        return 0
    
    return {"title": request.title, "summary": results[0]}

@router.get("/ChatHistoryByUser/{username}")
def get_chat_history_by_user(username: str):
    conn = connect_to_mysql()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # 유저 이름으로 필터링 후 session_id로 정렬, 그 안에서는 timestamp로 정렬
    query = """
        SELECT session_id, role, message, timestamp
        FROM chat_history
        WHERE username = %s
        ORDER BY session_id, timestamp;
    """
    cursor.execute(query, (username,))
    results = cursor.fetchall()

    conn.close()

    # session_id 기준으로 그룹핑
    history = {}
    for row in results:
        session_id = row["session_id"]
        if session_id not in history:
            history[session_id] = []
        history[session_id].append({
            "role": row["role"],
            "message": row["message"],
            "timestamp": row["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        })

    return {"username": username, "sessions": history}

@router.get("/GetChatHistoryBySession")
def get_chat_history_by_session(username: str, session_id: str):
    conn = connect_to_mysql()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            query = """
                SELECT role, message, timestamp
                FROM chat_history
                WHERE username = %s AND session_id = %s
                ORDER BY timestamp ASC
            """
            cursor.execute(query, (username, session_id))
            rows = cursor.fetchall()
                    # 🔥 datetime -> str 변환
            for row in rows:
                if isinstance(row["timestamp"], datetime):
                    row["timestamp"] = row["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        return JSONResponse(content=rows)
    finally:
        conn.close()

@router.delete("/DeleteChatSession")
def delete_chat_session(username: str, session_id: str):
    conn = connect_to_mysql()
    try:
        with conn.cursor() as cursor:
            # 세션 삭제
            query = """
                DELETE FROM chat_history
                WHERE username = %s AND session_id = %s
            """
            cursor.execute(query, (username, session_id))
            conn.commit()

        return {"status": "success", "message": f"세션 {session_id} 삭제 완료"}
    finally:
        conn.close()
