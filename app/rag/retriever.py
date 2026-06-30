from typing import Optional
from uuid import UUID

from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import settings
from app.db.services import ChunkService

# Fetch more candidates than needed so reranking has signal to work with
_FETCH_K_MULTIPLIER = 4


class Retriever:
    _embedding_model = None
    _reranker = None

    @classmethod
    def init(cls):
        if cls._embedding_model is None:
            cls._embedding_model = GoogleGenerativeAIEmbeddings(
                model=settings.GEMINI_EMBEDDING_MODEL,
                output_dimensionality=settings.EMBEDDING_DIM
            )
        return cls._embedding_model

    @classmethod
    def init_reranker(cls):
        """Lazy-load the cross-encoder. Call once at startup if reranking is enabled."""
        if cls._reranker is None:
            from sentence_transformers import CrossEncoder  # optional dependency
            cls._reranker = CrossEncoder(settings.RERANKER_MODEL)
        return cls._reranker

    @classmethod
    async def get(
        cls,
        db,
        user_id: UUID,
        query: str,
        top_k: int = 5,
        use_hybrid: bool = True,
        use_reranker: bool = False,
        metadata_filter: Optional[dict] = None,
    ) -> list[Document]:
        query_embedding = await cls._embedding_model.aembed_query(query)
        fetch_k = top_k * _FETCH_K_MULTIPLIER if use_reranker else top_k

        if use_hybrid:
            chunks = await ChunkService(db).hybrid_search(
                user_id=user_id,
                embedding=query_embedding,
                query_text=query,
                limit=fetch_k,
                fetch_k=max(fetch_k * 2, 20),
                metadata_filter=metadata_filter,
            )
        else:
            chunks = await ChunkService(db).similarity_search(
                user_id=user_id,
                embedding=query_embedding,
                limit=fetch_k,
                metadata_filter=metadata_filter,
            )

        if use_reranker and chunks:
            chunks = cls._rerank(query, chunks, top_k)

        return [
            Document(page_content=c.content, metadata=c.metadata_ or {})
            for c in chunks[:top_k]
        ]

    @classmethod
    def _rerank(cls, query: str, chunks, top_k: int):
        """Score (query, passage) pairs with a cross-encoder and return top_k."""
        reranker = cls._reranker
        pairs = [(query, c.content) for c in chunks]
        scores = reranker.predict(pairs)
        ranked = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
        return [c for _, c in ranked[:top_k]]