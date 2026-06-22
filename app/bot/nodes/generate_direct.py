from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from app.bot import RAGState
from app.bot.llm import llm_model
from app.bot.nodes.utils import stream_chunks, StreamResponseDTO, \
    upsert_db_with_messages
from app.core import logger


async def generate_direct(state: RAGState, config: RunnableConfig):
    logger.info("Generating a direct answer...")
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(
            "You are a helpful assistant\n"
            "Answer the question using only your general knowledge.\n"
            "DO NOT assume access to external documents.\n"
            "If you are unsure or the answer requires specific sources, say:\n"
            "'I don't know based on my general knowledge"
        ),
        HumanMessage(state["question"])
    ])

    chain = prompt | llm_model

    config_data = config["configurable"]
    stream_response: StreamResponseDTO = await stream_chunks(
        queue=config_data["stream_queue"],
        chain=chain,
        chain_input={}
    )

    await upsert_db_with_messages(state, config_data, stream_response)

    return {
        "messages": [
            HumanMessage(state["question"]),
            AIMessage(stream_response.answer_str)
        ]
    }
