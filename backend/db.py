from fastapi import APIRouter
from .models import ChatLog, SummaryLog, CheckRequest
import pymysql

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