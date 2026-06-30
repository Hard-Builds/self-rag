from datetime import datetime
from typing import List, Literal, Optional, TypedDict

from langchain_core.documents import Document
from langgraph.graph import MessagesState


class MetadataFilter(TypedDict, total=False):
    doc_type: Optional[str]
    source: Optional[str]
    uploaded_after: Optional[datetime]
    uploaded_before: Optional[datetime]


class RAGState(MessagesState):
    question: str
    answer: str

    # Question rewriting
    retrieval_query: str
    rewrite_tries: int

    need_retrieval: bool
    docs: List[Document]
    relevant_docs: List[Document]
    context_str: str

    answer_relevance: Literal[
        "FULLY_SUPPORTED", "PARTIALLY_SUPPORTED", "NOT_SUPPORTED"
    ]

    # answer rewriting
    ans_iteration: int

    # Answer usefulness
    is_ans_useful: bool
    reason: str

    metadata_filter: Optional[MetadataFilter]
