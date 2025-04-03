from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_huggingface import HuggingFaceEmbeddings
import search
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

def SetData(json_Data):
    results = []

    for data in json_Data:
        temp = {}
        temp['paperId'] = data['paperId']
        temp['title'] = data['title']
        temp['abstract'] = data['abstract']

        results.append(temp)

    return results

def CheckSimilarity(json_Data):
    # ✅ 데이터 (title + abstract 결합)
    documents = [
        Document(
            page_content=f"{item['title']}\n\n{item['abstract'] or ''}", 
            metadata={"paperId": item["paperId"], "title": item["title"]}
        )
        for item in json_Data
    ]

    # ✅ 임베딩 모델
    embeddingsModel = HuggingFaceEmbeddings(model_name='sentence-transformers/msmarco-distilbert-dot-v5')

    # ✅ FAISS 인덱스 생성
    retriever = FAISS.from_documents(documents, embeddingsModel).as_retriever(search_kwargs={'k': 7})

    # ✅ Reranker 모델
    model = HuggingFaceCrossEncoder(model_name='BAAI/bge-reranker-v2-m3')
    compressor = CrossEncoderReranker(model=model, top_n=3)

    # ✅ 압축 검색기 (Reranker 적용)
    compression_retriever = ContextualCompressionRetriever(base_compressor=compressor, base_retriever=retriever)

    compressed_docs = compression_retriever.invoke('AI ethics')

    return compressed_docs

if __name__ == '__main__':
    client = OpenAI()
    query = 'Attention is all you need에 대해서 알고싶어요'

    search_Query, user_Request = search.KeywordAndTranslate(query, client)
    print(search_Query, user_Request)

    json_Data = search.FindBySearchQuery(search_Query)

    results = SetData(json_Data)

    sim = CheckSimilarity(results)
    for data in sim:
        print(data.page_content)