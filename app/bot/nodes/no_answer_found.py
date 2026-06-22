from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from app.bot import RAGState
from app.bot.llm import llm_model
from app.bot.nodes.utils import stream_chunks, StreamResponseDTO, \
    upsert_db_with_messages
from app.core import logger


async def no_answer_found(state: RAGState, config: RunnableConfig):
    logger.info("No answer found...")
    question = state["question"]
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(
            "You are a helpful assistant.\n"
            "User has asked a question, but unfortunately you don't have "
            "enough context to answer the question.\n"
            "Reply with an apology, keep it short."
        ),
        HumanMessage(question)
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
            HumanMessage(question),
            AIMessage(stream_response.answer_str)
        ]
    }
