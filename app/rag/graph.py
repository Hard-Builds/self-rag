import asyncio

from langgraph.graph import StateGraph

from app.bot import RAGState


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
        graph = builder.compile(checkpointer=checkpointer)
        return graph