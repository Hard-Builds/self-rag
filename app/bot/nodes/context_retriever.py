from langchain_core.runnables import RunnableConfig

from app.bot import RAGState
from app.core import logger
from app.rag.retriever import Retriever


async def context_retriever(state: RAGState, config: RunnableConfig):
    logger.info("Retrieving context...")
    config = config["configurable"]
    context_docs = await Retriever.get(
        db=config["db"],
        user_id=config["user_id"],
        query=state.get("retrieval_query") or state["question"],
        top_k=3
    )
    return {"docs": context_docs}
