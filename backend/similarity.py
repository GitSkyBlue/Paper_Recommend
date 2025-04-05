from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
from fastapi import APIRouter
from .models import SimilarityRequest

load_dotenv()

router = APIRouter()

# 전역 변수
embeddings_model = None
reranker_model = None
compressor = None

@router.on_event("startup")
def load_models():
    global embeddings_model, reranker_model, compressor
    print("🔧 모델 로딩 중...")
    embeddings_model = HuggingFaceEmbeddings(model_name='sentence-transformers/msmarco-distilbert-dot-v5')
    reranker_model = HuggingFaceCrossEncoder(model_name='BAAI/bge-reranker-v2-m3')
    compressor = CrossEncoderReranker(model=reranker_model, top_n=5)
    print("✅ 모델 로딩 완료!")

# ✅ POST 방식 API
@router.post("/CheckSimilarity")
def check_similarity(request: SimilarityRequest):
    try:
        # ✅ Document 변환
        documents = [
            Document(
                page_content=f"{item.title}\n\n{item.abstract or ''}",
                metadata={"paperId": item.paperId, "title": item.title}
            )
            for item in request.json_data
        ]

        # ✅ FAISS 인덱스 생성
        retriever = FAISS.from_documents(documents, embeddings_model).as_retriever(search_kwargs={'k': 10})

        # ✅ 압축 검색기 (Reranker 적용)
        compression_retriever = ContextualCompressionRetriever(base_compressor=compressor, base_retriever=retriever)

        compressed_docs = compression_retriever.invoke(request.search_query)
        # print(compressed_docs)
        return compressed_docs

    except Exception as e:
        print("❌ 에러 발생:", e)
        return {"error": "유사도 분석 중 오류가 발생했습니다."}

    
if __name__ == '__main__':
    pass