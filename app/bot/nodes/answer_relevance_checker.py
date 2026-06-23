from typing import Literal

from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel

from app.bot import RAGState
from app.bot.llm import llm_model, str_parser
from app.core import logger


class AnswerRelevance(BaseModel):
    decision: Literal[
        "FULLY_SUPPORTED", "PARTIALLY_SUPPORTED", "NOT_SUPPORTED"
    ]


async def answer_relevance_checker(state: RAGState):
    logger.info("Checking answer relevance...")

    question = state["question"]
    answer = state["answer"]
    context = state["context_str"]

    response: AnswerRelevance = await llm_model.with_structured_output(
        AnswerRelevance).ainvoke([
        SystemMessage(
            "You are a strict judge, who reviews the given question and the answer generated.\n"
            "You need to provide answer from these three only:\n"
            "- FULLY_SUPPORTED:\n"
            "  Every meaningful claim is explicitly supported by CONTEXT, and the ANSWER does NOT introduce\n"
            "  any qualitative/interpretive words that are not present in CONTEXT.\n"
            "  (Examples of disallowed words unless present in CONTEXT: culture, generous, robust, designed to,\n"
            "  supports professional development, best-in-class, employee-first, etc.)\n\n"
            "- PARTIALLY_SUPPORTED:\n"
            "  The core facts are supported, BUT the ANSWER includes ANY abstraction, interpretation, or qualitative\n"
            "  phrasing not explicitly stated in CONTEXT (e.g., calling policies 'culture', saying leave is 'generous',\n"
            "  or inferring outcomes like 'supports professional development').\n\n"
            "- NOT_SUPPORTED:\n"
            "  The key claims are not supported by CONTEXT.\n\n"
            "Rules:\n"
            "- Be strict: if you see ANY unsupported qualitative/interpretive phrasing, choose partially_supported.\n"
            "- If the answer is mostly unrelated to the question or unsupported, choose no_support.\n"
            "- Evidence: include up to 3 short direct quotes from CONTEXT that support the supported parts.\n"
            "- Do not use outside knowledge."
        ),
        HumanMessage(
            f"Question: \n{question}\n\n"
            f"Answer: \n{answer}\n\n"
            f"Context: \n{context}\n\n"
        )
    ])
    return {"answer_relevance": response.decision}
