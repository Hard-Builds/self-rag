from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel

from app.bot import RAGState
from app.bot.llm import llm_model
from app.core import logger


class AnswerUsefulModel(BaseModel):
    is_ans_useful: bool
    reason: str


async def check_answer_usefulness(state: RAGState):
    logger.info("Checking for the answer's usefulness...")
    response: AnswerUsefulModel = await llm_model.with_structured_output(
        AnswerUsefulModel
    ).ainvoke([
        SystemMessage(
            "You are judging USEFULNESS of the answer for the QUESTION.\n\n"
            "Goal: \n"
            "- Decide if the answer actually addresses what the user asked.\n\n"
            "Rules: \n"
            "- is_ans_useful=True, The answer directly answers the question or provide the requested specific info.\n"
            "- is_ans_useful=False, The answer is generic, off-topic, or only gives related background without answering.\n"
            "- DO NOT use outside knowledge.\n"
            "- DO NOT re-check grounding. Only check: 'did we answer the question?'\n"
            "- Keep reason short to 1 line"
        ),
        HumanMessage(
            f"Question: {state["question"]}\n\n"
            f"Answer: {state["answer"]}"
        )
    ])
    return {
        "is_ans_useful": response.is_ans_useful,
        "reason": response.reason
    }
