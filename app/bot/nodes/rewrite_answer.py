from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, \
    HumanMessagePromptTemplate

from app.bot import RAGState
from app.bot.llm import llm_model, str_parser
from app.core import logger

_MAX_ANS_ITERATION = 3


async def rewrite_answer_router(state: RAGState):
    if state["answer_relevance"] == "FULLY_SUPPORTED":
        return "check_answer_usefulness"

    if state["ans_iteration"] < _MAX_ANS_ITERATION:
        return "rewrite_answer"

    return "check_answer_usefulness"

async def rewrite_answer(state: RAGState):
    logger.info("Rewriting answer...")

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(
            "You are a strict reviser.\n\n"
            "You must output based on the following format:\n\n"
            "FORMAT (quote-only answer):\n"
            "- <direct quote from the CONTEXT>\n"
            "- <direct quote from the CONTEXT>\n\n"
            "Rules: \n"
            "- Use ONLY the CONTEXT.\n"
            "- Do NOT add any new words besides bullet dashes and the quotes themselves.\n"
            "- Do NOT explain anything.\n"
            "-Do NOT say 'context', 'not mentioned', 'does not mention', 'not provided' etc"
        ),
        HumanMessagePromptTemplate.from_template(
            "Question: \n{question}\n\n"
            "Answer: \n{answer}\n\n"
            "Context: \n{context}\n\n"
        )
    ])
    chain = prompt | llm_model | str_parser
    response = await chain.ainvoke({
        "question": state["question"],
        "answer": state["answer"],
        "context": state["context_str"]
    })
    return {
        "answer": response,
        "ans_iteration": state["ans_iteration"] + 1
    }
