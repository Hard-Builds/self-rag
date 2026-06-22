from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, \
    HumanMessagePromptTemplate
from pydantic import BaseModel, Field

from app.bot import RAGState
from app.bot.llm import llm_model
from app.core import logger


class NeedRetrievalModel(BaseModel):
    need_retrieval: bool = Field(
        description="Provide true if context retrieval is needed, else False"
    )


async def decide_retrieve(state: RAGState):
    logger.info("Deciding the RAG usage...")
    llm = llm_model.with_structured_output(NeedRetrievalModel)
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(
            "You are a strict retrieval evaluator for RAG.\n"
            "You decide whether retrieval is needed.\n"
            "Return JSON that matches this schema:\n"
            "{{'need_retrieval': boolean}}\n\n"
            "Guidelines: \n"
            "- need_retrieval=True if answering requires specific facts, citations, or info likely not in the model\n"
            "- need_retrieval=False for general explanations, definitions or reasoning that does not need sources\n"
            "- If unsure, choose True."
        ),
        HumanMessagePromptTemplate.from_template("Question: {question}")
    ])
    chain = prompt | llm

    response: NeedRetrievalModel = await chain.ainvoke(
        {"question": state["question"]})
    return {"need_retrieval": response.need_retrieval}
