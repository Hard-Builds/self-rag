import uuid
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert

from app.db.models import Document
from app.db.models.chunk import Chunk
from app.db.services.base import BaseDB

# Reciprocal Rank Fusion constant — 60 is the standard default
_RRF_K = 60


class ChunkService(BaseDB[Chunk]):
    def __init__(self, db):
        super().__init__(db, Chunk)

    async def upsert_many(
        self,
        rows: List[Dict[str, Any]],
        batch_size: int = 100,
        commit: bool = True,
    ) -> None:
        """Bulk-upsert chunks in batches.

        Conflict target is (document_id, chunk_index). On conflict the content,
        embedding, and metadata columns are updated so re-ingesting a document
        is idempotent.
        """
        for start in range(0, len(rows), batch_size):
            batch = rows[start : start + batch_size]
            stmt = insert(Chunk).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=["document_id", "chunk_index"],
                set_={
                    "content": stmt.excluded.content,
                    "embedding": stmt.excluded.embedding,
                    "metadata_": stmt.excluded.metadata_,
                },
            )
            await self.db.execute(stmt)
            await self.db.flush()
        if commit:
            await self.db.commit()

    async def get_chunks_for_document(self, document_id: uuid.UUID):
        return await self.get_all_by_filter(document_id=document_id)

    async def similarity_search(self, user_id: UUID, embedding: list[float],
                                limit: int = 5) -> list[Chunk]:
        # cosine_distance works best for normalized embeddings (most semantic models)
        # swap to .l2_distance() if your model outputs unnormalized vectors
        stmt = (
            select(Chunk)
            .join(Document, Chunk.document_id == Document.id)
            .filter(Document.user_id == user_id)
            .order_by(Chunk.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def hybrid_search(
        self,
        user_id: UUID,
        embedding: list[float],
        query_text: str,
        limit: int = 5,
        fetch_k: int = 20,
    ) -> list[Chunk]:
        """Reciprocal Rank Fusion over dense (cosine) + sparse (BM25/ts_rank) results.

        fetch_k candidates are retrieved per leg before fusion so the final
        ranking has enough signal. Only `limit` rows are returned.
        """
        # Dense leg — ranked by cosine distance ascending (lower = closer)
        dense_cte = (
            select(
                Chunk.id,
                func.row_number()
                .over(order_by=Chunk.embedding.cosine_distance(embedding))
                .label("dense_rank"),
            )
            .join(Document, Chunk.document_id == Document.id)
            .filter(Document.user_id == user_id)
            .filter(Chunk.embedding.isnot(None))
            .order_by(Chunk.embedding.cosine_distance(embedding))
            .limit(fetch_k)
            .cte("dense_cte")
        )

        # Sparse leg — PostgreSQL full-text search ranked by ts_rank
        ts_query = func.plainto_tsquery("english", query_text)
        ts_vector = func.to_tsvector("english", Chunk.content)
        sparse_cte = (
            select(
                Chunk.id,
                func.row_number()
                .over(order_by=func.ts_rank(ts_vector, ts_query).desc())
                .label("sparse_rank"),
            )
            .join(Document, Chunk.document_id == Document.id)
            .filter(Document.user_id == user_id)
            .filter(ts_vector.op("@@")(ts_query))
            .order_by(func.ts_rank(ts_vector, ts_query).desc())
            .limit(fetch_k)
            .cte("sparse_cte")
        )

        # RRF fusion: score = 1/(k+rank_dense) + 1/(k+rank_sparse)
        # COALESCE handles chunks that appear in only one leg (rank defaults to fetch_k+1)
        rrf_score = (
            1.0 / (_RRF_K + func.coalesce(dense_cte.c.dense_rank, fetch_k + 1))
            + 1.0 / (_RRF_K + func.coalesce(sparse_cte.c.sparse_rank, fetch_k + 1))
        )
        fused_cte = (
            select(
                func.coalesce(dense_cte.c.id, sparse_cte.c.id).label("chunk_id"),
                rrf_score.label("rrf_score"),
            )
            .select_from(
                dense_cte.outerjoin(sparse_cte, dense_cte.c.id == sparse_cte.c.id)
            )
            .union(
                select(
                    func.coalesce(sparse_cte.c.id, dense_cte.c.id).label("chunk_id"),
                    rrf_score.label("rrf_score"),
                )
                .select_from(
                    sparse_cte.outerjoin(dense_cte, sparse_cte.c.id == dense_cte.c.id)
                )
            )
            .cte("fused_cte")
        )

        stmt = (
            select(Chunk)
            .join(fused_cte, Chunk.id == fused_cte.c.chunk_id)
            .order_by(fused_cte.c.rrf_score.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
