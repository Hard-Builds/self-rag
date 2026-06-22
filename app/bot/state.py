from typing import List, Literal

from langchain_core.documents import Document
from langgraph.graph import MessagesState


class RAGState(MessagesState):
    question: str

    need_retrieval: bool
    docs: List[Document]
    relevant_docs: List[Document]

    answer_relevance: Literal[
        "FULLY_SUPPORTED", "PARTIALLY_SUPPORTED", "NOT_SUPPORTED"
    ]
