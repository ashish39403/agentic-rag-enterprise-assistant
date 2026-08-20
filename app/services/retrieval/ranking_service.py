import json
import os
import re

import logfire
from dotenv import load_dotenv
from langfuse.openai import openai

from app.config import settings

load_dotenv()

RERANK_MODEL = os.getenv("RERANK_MODEL", settings.LLM_MODEL)

client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    
)


def _extract_json_array(text: str) -> list[int]:
    """
    Extract a JSON array like [0, 2, 4] from the LLM response.
    """
    match = re.search(r"\[[\d,\s]+\]", text)
    if not match:
        return []

    try:
        data = json.loads(match.group(0))
        return [int(x) for x in data]
    except Exception:
        return []


def rerank_documents(query: str, documents: list[str], top_n: int = 5) -> list[str]:
    """
    API-based LLM reranker.

    Input:
      query = user/search query
      documents = Qdrant retrieved chunks

    Output:
      top_n most relevant chunks in reranked order
    """
    if not documents:
        return []

    try:
        chunk_text = ""

        for i, doc in enumerate(documents):
            safe_doc = doc[:1200]
            chunk_text += f"\n[{i}]\n{safe_doc}\n"

        prompt = f"""
You are a document reranker for a RAG system.

Task:
Given a user query and candidate document chunks, return the indexes of the {top_n} most relevant chunks.

Rules:
- Return only a JSON array of integers.
- Do not explain.
- Prefer chunks that directly answer the query.
- Ignore unrelated/noisy chunks.

User query:
{query}

Candidate chunks:
{chunk_text}

Return format example:
[2, 0, 5, 1, 3]
"""

        with logfire.span("LLM API Reranking", candidates=len(documents), top_n=top_n):
            response = client.chat.completions.create(
                model=RERANK_MODEL,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
            )

        content = response.choices[0].message.content or ""
        ranked_indexes = _extract_json_array(content)

        reranked_docs = []
        seen = set()

        for idx in ranked_indexes:
            if 0 <= idx < len(documents) and idx not in seen:
                reranked_docs.append(documents[idx])
                seen.add(idx)

            if len(reranked_docs) >= top_n:
                break

        if reranked_docs:
            logfire.info(f"LLM reranking selected {len(reranked_docs)} chunks.")
            return reranked_docs

        logfire.warning("LLM reranking returned no valid indexes. Falling back to Qdrant order.")
        return documents[:top_n]

    except Exception as e:
        logfire.error("LLM reranking failed: {error}", error=str(e))
        return documents[:top_n]
