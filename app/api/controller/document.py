import os
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile
from starlette import status

from app.core import logger
from app.db.services import DocumentService
from app.worker import tasks

UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class DocumentController:
    def __init__(self, db):
        self.db = db
        self.document_service = DocumentService(db)

    async def get_document(self, user_id: UUID, document_id: UUID):
        return await self.document_service.get_by_filter(
            id=document_id,
            user_id=user_id
        )

    async def list_all_documents(self, user_id: UUID):
        document_list = await self.document_service.get_all_by_filter(
            user_id=user_id)
        return document_list

    async def delete_document(self, user_id: UUID, document_id: UUID):
        document = await self.document_service.get_by_filter(
            id=document_id,
            user_id=user_id
        )
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        await self.document_service.delete_by_id(id=document_id)
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
            logger.info(f"Deleted local file: {document.file_path}")

        logger.info(f"Deleted : {document_id}")

    async def handle_document_ingestion(
            self,
            file: UploadFile,
            user_id: UUID
    ):
        filename: str = file.filename
        user_upload_dir = UPLOAD_DIR / str(user_id)
        os.makedirs(user_upload_dir, exist_ok=True)
        file_path: str = str(user_upload_dir / filename)

        if await self.document_service.is_ingested(
                user_id=user_id,
                filename=filename
        ):
            raise Exception("Given file is already processed")

        # Currently only supported for pdf
        await self._validate_pdf_doc(file)

        MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds the 2 MB limit"
            )

        # Storing file locally
        with open(file_path, "wb") as tmp:
            tmp.write(content)

        # Updating DB with the records
        document = await self.document_service.create({
            "user_id": user_id,
            "filename": filename,
            "file_path": file_path
        })

        tasks.ingest_document.delay(
            document_id=document.id,
            user_id=user_id,
            filename=filename,
            file_path=file_path
        )

    async def _validate_pdf_doc(self, file):
        if not file.filename.endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files allowed"
            )

        content = await file.read(4)
        if not content.startswith(b"%PDF"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file"
            )

        await file.seek(0)
