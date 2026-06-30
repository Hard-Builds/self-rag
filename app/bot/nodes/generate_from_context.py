from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, \
    HumanMessagePromptTemplate

from app.bot import RAGState
from app.core import logger
from app.bot.llm import llm_model, str_parser


async def generate_from_context(state: RAGState):
    logger.info("Generating response with context...")
    question = state["question"]
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(
            # v2 — structured fallback, format guidance, ambiguous query and partial context guardrails
            "You are a business Q&A assistant. Answer the user's question using ONLY the provided CONTEXT.\n\n"
            "Format:\n"
            "- Answer in 1–3 concise sentences. Do not use bullet points unless listing distinct items.\n"
            "- Do not start with 'Based on the context' or 'According to the document'.\n"
            "- Do not use outside knowledge.\n\n"
            "Edge case guardrails:\n"
            "- CONTEXT is empty or clearly unrelated → respond: "
            "'I was unable to find specific information about this in the available documents.'\n"
            "- CONTEXT partially answers the question (covers one part, silent on another) → answer only "
            "the part covered; do not speculate on the rest.\n"
            "- Question is ambiguous (could mean two things) → answer the most specific, literal interpretation "
            "supported by CONTEXT.\n"
            "- CONTEXT contains conflicting statements → state both without resolving the conflict.\n"
            "- CONTEXT is from a policy/pricing document but the question is about a different time period "
            "or version → answer using the available information without assuming it is current."
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
