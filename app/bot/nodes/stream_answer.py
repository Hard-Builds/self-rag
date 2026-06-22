from langchain_core.runnables import RunnableConfig

from app.bot import RAGState
from app.bot.nodes.utils import upsert_db_with_messages, StreamResponseDTO


async def stream_answer(state: RAGState, config: RunnableConfig):
    config_data = config["configurable"]
    queue = config_data["stream_queue"]

    await queue.put(state["answer"])
    await queue.put(None)

    await upsert_db_with_messages(
        state=state,
        config_data=config_data,
        stream_response=StreamResponseDTO(
            latency_ms=0,
            answer_str=state["answer"],
            full_response=None
        )
    )
    return {}
