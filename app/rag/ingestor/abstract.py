import asyncio
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from langchain_core.documents import Document
from langchain_experimental.text_splitter import SemanticChunker
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tenacity import retry, wait_exponential, stop_after_attempt, \
    retry_if_exception

from app.constants import DocumentStatusEnum
from app.core import settings, logger
from app.db.services import DocumentService, ChunkService


def _is_rate_limit_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return "429" in msg or "quota" in msg or "resource exhausted" in msg


def _is_transient_db_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return any(kw in msg for kw in (
        "connection", "timeout", "deadlock", "could not connect",
        "server closed the connection", "operationalerror",
    ))

class BaseIngestor(ABC):
    _embedding_model = None

    def __init__(
            self,
            db,
            user_id: str | UUID,
            document_id: str | UUID,
            filename: str,
            file_path: str,
            chunk_size: int = settings.CHUNK_SIZE,
            chunk_overlap: int = settings.CHUNK_OVERLAP
    ):
        self.user_id = user_id
        self.document_id = document_id
        self.filename = filename
        self.file_path = file_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_batch_size = settings.EMBEDDING_BATCH_SIZE
        self.doc_service = DocumentService(db)
        self.chunk_service = ChunkService(db)

    @property
    def _embedder(self):
        if not getattr(self, "_embedding_model", None):
            self._embedding_model = GoogleGenerativeAIEmbeddings(
                model=settings.GEMINI_EMBEDDING_MODEL,
                output_dimensionality=settings.EMBEDDING_DIM
            )
        return self._embedding_model

    async def ainvoke(self, is_final_attempt: bool = True):
        try:
            # Loading data
            docs = await self._load_documents()

            # Chunking data
            chunks = await self._split_documents(docs)
            logger.info(
                f"[{self.document_id}] : Found {len(chunks)} document_chunks"
            )

            # Embedding and store data
            await self._embed_and_store(chunks)

            await self._document_status_update(DocumentStatusEnum.COMPLETED)
        except Exception as exc:
            logger.error(f"Something went wrong while processing document "
                         f"{self.document_id} : {exc}")
            # Only persist a terminal FAILED status once no further retries will
            # happen (caller is out of attempts) — otherwise leave the row as
            # PROCESSING since a retry is still pending.
            if is_final_attempt:
                await self._document_status_update(
                    status=DocumentStatusEnum.FAILED,
                    error_msg=str(exc)
                )
            raise exc

    @abstractmethod
    async def _load_documents(self) -> list[Document]:
        pass

    async def _split_documents(self, docs: list[Document]) -> list[Document]:
        if settings.SEMANTIC_CHUNKING:
            splitter = SemanticChunker(
                embeddings=self._embedder,
                breakpoint_threshold_type=settings.SEMANTIC_CHUNKING_BREAKPOINT_TYPE,
            )
        else:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
        chunks = splitter.split_documents(documents=docs)
        return chunks

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(5),
        retry=retry_if_exception(_is_rate_limit_error)
    )
    async def _embed_batch(self, texts):
        return await self._embedder.aembed_documents(texts)

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(settings.DB_INSERT_MAX_RETRIES),
        retry=retry_if_exception(_is_transient_db_error),
        reraise=True,
    )
    async def _store_batch(self, rows: list[dict]) -> None:
        await self.chunk_service.upsert_many(
            rows,
            batch_size=settings.DB_INSERT_BATCH_SIZE,
            commit=False,
        )

    async def _embed_and_store(self, chunks: list[Document]):
        emb_batch_size = self.embedding_batch_size
        total = len(chunks)

        for idx in range(0, total, emb_batch_size):
            batch_chunks = chunks[idx: idx + emb_batch_size]
            texts = [c.page_content for c in batch_chunks]

            batch_embeddings = await self._embed_batch(texts)

            rows = [
                {
                    "document_id": self.document_id,
                    "content": chunk.page_content,
                    "embedding": embedding,
                    "chunk_index": idx + offset,
                    "metadata_": chunk.metadata,
                }
                for offset, (chunk, embedding) in enumerate(
                    zip(batch_chunks, batch_embeddings)
                )
            ]
            await self._store_batch(rows)

            processed = min(idx + emb_batch_size, total)
            logger.info(f"[{self.document_id}] chunks persisted: {processed}/{total}")

            if processed < total:
                await asyncio.sleep(5)

    async def _document_status_update(
            self,
            status: DocumentStatusEnum,
            error_msg: Optional[str] = None
    ):
        update_info = {"status": status}
        if error_msg:
            update_info["error"] = str(error_msg)
        await self.doc_service.update(
            _id=self.document_id,
            obj_in=update_info
        )
