"""Prompt templates for the RAG chain."""
from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate


SYSTEM_TEMPLATE = """You are an expert epidemiologist assistant specializing in \
hantavirus and the MV Hondius outbreak. Answer using ONLY the provided context below.

Rules:
- Cite every factual claim using the source number in brackets, e.g. [1], [2].
- If the context does not contain the answer, say clearly: \
"I don't have sufficient information in my sources to answer this question."
- Be factual, concise, and accessible to journalists and health workers.
- Do not speculate beyond the provided context.
- When citing statistics or case counts, always note the date of the source.

Context:
{context}

Sources available:
{sources_list}"""

HUMAN_TEMPLATE = "{question}"


def build_rag_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(SYSTEM_TEMPLATE),
        HumanMessagePromptTemplate.from_template(HUMAN_TEMPLATE),
    ])


STARTER_QUESTIONS = [
    "What is the Andes strain and why is it considered dangerous?",
    "How many cases are confirmed on MV Hondius?",
    "Can Andes virus spread human to human?",
    "What is the mortality rate of hantavirus pulmonary syndrome?",
    "What are the symptoms of Andes virus infection?",
    "What is the current status of the MV Hondius outbreak?",
    "How is hantavirus transmitted to humans?",
    "What treatments exist for hantavirus pulmonary syndrome?",
]
