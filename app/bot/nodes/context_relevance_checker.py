import asyncio

from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, \
    HumanMessagePromptTemplate
from pydantic import BaseModel, Field

from app.bot import RAGState
from app.bot.llm import llm_model, str_parser
from app.core import logger


class RelevanceCheckerModel(BaseModel):
    is_relevant: bool = Field(
        description="True, if the given document is relevant to answer the "
                    "question, else False"
    )


async def context_relevance_checker(state: RAGState):
    logger.info("Checking doc relevance...")
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(
            "You are judging document relevance.\n"
            "Return JSON that matches this schema: \n"
            "{{'is_relevant': boolean}}\n\n"
            "A document is relevant if it contains information useful for "
            "answering the question"
        ),
        HumanMessagePromptTemplate.from_template(
            "Question: \n{question}\n\n"
            "Document: \n{document}"
        )
    ])
    llm = llm_model.with_structured_output(RelevanceCheckerModel)
    chain = prompt | llm

    coroutines = []
    for doc in state["docs"]:
        coroutines.append(chain.ainvoke({
            "question": state["question"],
            "document": doc.page_content
        }))

    decisions = await asyncio.gather(*coroutines)

    relevant_docs = []
    for doc, decision in zip(state["docs"], decisions):
        if decision.is_relevant:
            relevant_docs.append(doc)

    logger.info(f"Relevant docs found: {len(relevant_docs)}/"
                f"{len(state["docs"])}")
    return {"relevant_docs": relevant_docs}
