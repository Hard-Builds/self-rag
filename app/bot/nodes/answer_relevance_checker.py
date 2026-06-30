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
            # v2 — fallback string guardrails, consistent enum names, removed dead evidence instruction
            "You are a strict grounding judge. Decide if every claim in ANSWER is supported by CONTEXT.\n\n"
            "FULLY_SUPPORTED: Every meaningful claim is explicitly present in CONTEXT. No qualitative or\n"
            "interpretive words that are absent from CONTEXT.\n"
            "(Disallowed unless in CONTEXT: generous, robust, best-in-class, employee-first, culture,\n"
            "designed to, supports professional development, etc.)\n\n"
            "PARTIALLY_SUPPORTED: Core facts are supported, but ANSWER adds abstraction, interpretation,\n"
            "or qualitative phrasing not in CONTEXT.\n\n"
            "NOT_SUPPORTED: Key claims are not present in CONTEXT, or ANSWER is unrelated to QUESTION.\n\n"
            "Edge case guardrails:\n"
            "- ANSWER is exactly 'No relevant document found' or 'I don't know' → NOT_SUPPORTED\n"
            "- ANSWER is empty or blank → NOT_SUPPORTED\n"
            "- CONTEXT is empty but ANSWER makes factual claims → NOT_SUPPORTED\n"
            "- ANSWER correctly states there is no information available → FULLY_SUPPORTED\n"
            "- ANSWER answers a slightly different question using valid CONTEXT facts → PARTIALLY_SUPPORTED\n\n"
            "Rules:\n"
            "- Be strict: ANY unsupported qualitative phrasing → PARTIALLY_SUPPORTED.\n"
            "- Do not use outside knowledge.\n"
            "- Return only the decision field — no explanation."
        ),
        HumanMessage(
            f"Question: \n{question}\n\n"
            f"Answer: \n{answer}\n\n"
            f"Context: \n{context}\n\n"
        )
    ])
    return {"answer_relevance": response.decision}
