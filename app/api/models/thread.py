from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.constants.enums import MessageRoleEnum


class MetadataFilter(BaseModel):
    doc_type: Optional[str] = None
    source: Optional[str] = None
    uploaded_after: Optional[datetime] = None
    uploaded_before: Optional[datetime] = None


# ------- Request models -------
class QueryRequest(BaseModel):
    query: str
    filters: Optional[MetadataFilter] = None

class ThreadListRespModel(BaseModel):
    id: UUID
    title: str

    model_config = ConfigDict(from_attributes=True)


class ThreadMessageListRespModel(BaseModel):
    id: UUID
    role: MessageRoleEnum
    content: str

    model_config = ConfigDict(from_attributes=True)
