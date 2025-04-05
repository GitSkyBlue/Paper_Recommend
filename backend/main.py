
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




# if __name__ == '__main__':
#     client = OpenAI()
#     query = 'Attention is all you need에 대해서 알고싶어요'
#     search_Query, user_Request = search.KeywordAndTranslate(query, client)
#     print('Search Query :', search_Query)
#     print('User Request :', user_Request)

#     json_Data = search.FindBySearchQuery(search_Query)
#     ###################################################

#     results = similarity.SetData(json_Data)

#     sim_list = similarity.CheckSimilarity(search_Query, results)

#     paper_infos = summary.FindIDAndURL(sim_list, json_Data)
#     print(paper_infos)
#     summary.DownloadPDF(paper_infos)
#     summary.Summarize(client)