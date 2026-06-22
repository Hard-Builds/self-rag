import asyncio

from langgraph.graph import StateGraph, START, END

from app.bot import RAGState
from app.bot.nodes import generate_direct, decide_retrieve, context_retriever, \
    upsert_thread, generate_from_context, no_answer_found, \
    answer_relevance_checker, context_relevance_checker, rewrite_answer, \
    stream_answer


class RAGGraph:
    _graph = None
    _lock = asyncio.Lock()

    @classmethod
    async def init(cls, checkpointer):
        async with cls._lock:
            if cls._graph is None:
                cls._graph = await cls._build(checkpointer=checkpointer)
        return cls._graph

    @classmethod
    async def _build(cls, checkpointer):
        builder = StateGraph(RAGState)

        builder.add_node("upsert_thread", upsert_thread)
        builder.add_node("should_retrieve", decide_retrieve)
        builder.add_node("generate_direct", generate_direct)
        builder.add_node("context_retriever", context_retriever)
        builder.add_node("context_relevance_checker",
                         context_relevance_checker)
        builder.add_node("no_answer_found", no_answer_found)
        builder.add_node("generate_from_context", generate_from_context)
        builder.add_node("answer_relevance_checker", answer_relevance_checker)
        builder.add_node("rewrite_answer", rewrite_answer)
        builder.add_node("stream_answer", stream_answer)

        builder.add_edge(START, "upsert_thread")
        builder.add_edge("upsert_thread", "should_retrieve")

        builder.add_conditional_edges(
            "should_retrieve",
            lambda state: state["need_retrieval"],
            {
                True: "context_retriever",
                False: "generate_direct"
            }
        )

        builder.add_edge("context_retriever", "context_relevance_checker")

        builder.add_conditional_edges(
            "context_relevance_checker",
            lambda state: len(state["relevant_docs"]) > 0,
            {
                True: "generate_from_context",
                False: "no_answer_found"
            }
        )
        builder.add_edge("generate_from_context", "answer_relevance_checker")

        builder.add_conditional_edges(
            "answer_relevance_checker",
            lambda state: state["answer_relevance"],
            {
                "FULLY_SUPPORTED": "stream_answer",
                "PARTIALLY_SUPPORTED": "rewrite_answer",
                "NOT_SUPPORTED": "rewrite_answer",
            }
        )

        builder.add_edge("rewrite_answer", "answer_relevance_checker")
        builder.add_edge("stream_answer", END)
        builder.add_edge("generate_direct", END)
        builder.add_edge("no_answer_found", END)

        graph = builder.compile(checkpointer=checkpointer)
        return graph