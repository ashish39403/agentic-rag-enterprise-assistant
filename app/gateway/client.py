import logfire
from langchain_openai import ChatOpenAI
from langfuse.openai import openai

from app.config import settings


def get_langchain_llm(feature: str = "rag") -> ChatOpenAI:
    """
    Return the chat model used by LangGraph nodes.

    Uses the direct OpenAI-compatible endpoint configured with:
      OPENAI_API_KEY
      OPENAI_BASE_URL
      LLM_MODEL
    """
    logfire.info(
        "LLM gateway mode: direct endpoint | feature={feature} | model={model}",
        feature=feature,
        model=settings.LLM_MODEL,
    )
    return ChatOpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        model=settings.LLM_MODEL,
        temperature=0,
    )


def create_chat_completion(messages: list, temperature: float = 0.1):
    """Create a chat completion through the direct OpenAI-compatible endpoint."""
    logfire.info(
        "Responder gateway mode: direct endpoint | model={model}",
        model=settings.LLM_MODEL,
    )

    client = openai.OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
    )

    return client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=messages,
        temperature=temperature,
    )


def extract_cache_status(response) -> str:
    """Direct provider responses do not include Portkey cache headers."""
    return "MISS"
