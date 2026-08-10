import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def _set_env_if_present(name: str) -> None:
    value = os.getenv(name)
    if value:
        os.environ[name] = value


class Settings:
    # --- OPENAI-COMPATIBLE API (LLM + EMBEDDINGS) ---
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
    LLM_MODEL = os.getenv("LLM_MODEL", "nvidia/nemotron-3-ultra-550b-a55b")

    # --- VECTOR DB (QDRANT) ---
    QDRANT_URL = os.getenv("QDRANT_CLUSTER_ENDPOINT")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    QDRANT_COLLECTION = "enterprise_rag"
    
    _set_env_if_present("LANGFUSE_SECRET_KEY")
    _set_env_if_present("LANGFUSE_PUBLIC_KEY")
    _set_env_if_present("LANGFUSE_BASE_URL")

    # # --- REASONING ENGINE (GROQ) ---
    # GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    # GROQ_MODEL = "llama-3.3-70b-versatile"
    # GROQ_FALLBACK_API_KEY = os.getenv("GROQ_FALLBACK_API_KEY")

    # --- LLM GATEWAY (PORTKEY) ---
    # Disabled for now. The app uses OPENAI_API_KEY + OPENAI_BASE_URL directly.
    PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY")
    # PORTKEY_CONFIG_ID = os.getenv("PORTKEY_CONFIG_ID")
  
    # GROQ_SLUG =  "rag"     # primary: @rag/llama-3.3-70b-versatile
    # GROQ_SLUG_2 = "brag"  # fallback: @brag/llama-3.1-8b-instant

    
    # --- OBSERVABILITY ---
    # LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "true")
    # LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
    # LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "rag_scale_test")
    # LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

# Apply LangChain environment variables for automatic tracing
#

settings = Settings()
