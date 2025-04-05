from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import search, similarity, summary

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 필요한 도메인만 열어두는 게 좋음
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router)
app.include_router(similarity.router)
app.include_router(summary.router)