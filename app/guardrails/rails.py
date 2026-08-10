import logfire
from typing import Optional, Tuple

from langchain_openai import ChatOpenAI
from nemoguardrails import LLMRails, RailsConfig

from app.config import settings
from app.guardrails.colang_rules import COLANG_CONTENT, RAIL_INDICATORS, YAML_CONTENT


_rails: Optional[LLMRails] = None


def initialize_rails() -> None:
    """
    Build the NeMo LLMRails singleton at app startup.

    Uses an OpenAI-compatible model endpoint for fast intent classification at
    the guardrail gate.
    """
    global _rails

    guard_llm = ChatOpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        model="nvidia/nemotron-3-nano-omni-30b-a3b",
        temperature=0,
    )

    config = RailsConfig.from_content(
        colang_content=COLANG_CONTENT,
        yaml_content=YAML_CONTENT,
    )

    _rails = LLMRails(config, llm=guard_llm)
    logfire.info("NeMo Guardrails initialized.")


def guard(message: str) -> Tuple[bool, Optional[str]]:
    """
    Run a user message through the NeMo rails gate.

    Returns:
        (True, rail_response) when a rail fired.
        (False, None) when the message should continue to LangGraph.
    """
    if _rails is None:
        logfire.warning("Guardrails not initialized; skipping gate.")
        return False, None

    with logfire.span("Guardrails Check"):
        result = _rails.generate(messages=[{"role": "user", "content": message}])

        content = result.get("content", "") if isinstance(result, dict) else str(result)
        fired = any(indicator in content for indicator in RAIL_INDICATORS)

        if fired:
            logfire.info(f"Guardrails fired | query='{message[:80]}'")
            return True, content

        logfire.info("Guardrails passed.")
        return False, None
