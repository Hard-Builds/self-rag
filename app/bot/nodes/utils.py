import asyncio
import time
from typing import Any

from langchain_core.runnables import RunnableSequence
from pydantic import BaseModel

from app.bot import RAGState
from app.bot.llm import str_parser
from app.constants.enums import MessageRoleEnum
from app.db.services import MessageService


class StreamResponseDTO(BaseModel):
    latency_ms: int
    answer_str: str
    full_response: Any


async def stream_chunks(
        queue: asyncio.Queue,
        chain: RunnableSequence,
        chain_input: dict
):
    start = time.monotonic()

    answer_str = ""
    full_response = None
    async for event in chain.astream_events(chain_input):
        if event["event"] == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            if chunk.content:
                chunk_content = await str_parser.ainvoke(chunk)
                answer_str += chunk_content
                await queue.put(chunk_content)

        elif event["event"] == "on_chat_model_end":
            full_response = event["data"]["output"]

    latency_ms = int((time.monotonic() - start) * 100)

    # Signaling the end of the stream
    await queue.put(None)

    return StreamResponseDTO(
        latency_ms=latency_ms,
        full_response=full_response,
        answer_str=answer_str
    )


async def upsert_db_with_messages(
        state: RAGState,
        config_data: dict,
        stream_response: StreamResponseDTO
):
    # Storing the messages
    db = config_data["db"]
    thread_id = config_data["thread_id"]

    metadata = getattr(stream_response.full_response, "usage_metadata", {})

    msg_service = MessageService(db)

    # Human Message
    await msg_service.create({
        "thread_id": thread_id,
        "role": MessageRoleEnum.HUMAN,
        "content": state["question"],
        "token_count": metadata.get("input_tokens")
    }, commit=False)

    # AI response Message
    await msg_service.create({
        "thread_id": thread_id,
        "role": MessageRoleEnum.AI,
        "content": stream_response.answer_str,
        "token_count": metadata.get("output_tokens"),
        "latency_ms": stream_response.latency_ms
    }, commit=False)

    
