from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, \
    HumanMessagePromptTemplate
from langchain_core.runnables import RunnableConfig
from sentry_sdk import logger

from app.bot import RAGState
from app.bot.llm import llm_model, str_parser


async def generate_from_context(state: RAGState):
    logger.info("Generating response with context...")
    question = state["question"]
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(
            "You are a business RAG assistant. \n"
            "Answer the given user's question with provided context ONLY.\n"
            "If the context does not contain enough information, say: \n"
            "'No relevant document found'\n"
            "Do not use outside knowledge."
        ),
        HumanMessagePromptTemplate.from_template(
            "Question: \n{question}\n\n"
            "Context: \n{context}"
        )
    ])
    chain = prompt | llm_model | str_parser
    response = await chain.ainvoke({
        "question": question,
        "context": state["context_str"]
    })

    return {"answer": response, "ans_iteration": 0}
