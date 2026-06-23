from typing import List, Literal

from langchain_core.documents import Document
from langgraph.graph import MessagesState


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
