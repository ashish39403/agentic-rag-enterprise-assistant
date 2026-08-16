import os
from contextlib import asynccontextmanager
from typing import Optional

import logfire
from dotenv import load_dotenv
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from langfuse import get_client, propagate_attributes
from langfuse.langchain import CallbackHandler
from pydantic import BaseModel


load_dotenv()


def configure_logfire() -> None:
    token = os.getenv("LOGFIRE_TOKEN")
    if not token:
        os.environ["LOGFIRE_IGNORE_NO_CONFIG"] = "1"
        print("LOGFIRE_TOKEN is not set; Logfire tracing is disabled.")
        return

    try:
        logfire.configure(token=token)
    except Exception as exc:
        print(f"Logfire configuration failed; tracing is disabled. Reason: {exc}")


configure_logfire()
langfuse = get_client()

from app.agents.graph import rag_agent
from app.guardrails import guard, initialize_rails


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI startup/shutdown lifecycle.

    Replaces deprecated @app.on_event("startup").
    """
    try:
        initialize_rails()
    except Exception as e:
        logfire.error("Guardrails initialization failed: {error}", error=str(e))
    yield
    langfuse.flush()


app = FastAPI(
    title="Enterprise Agentic RAG API",
    lifespan=lifespan,
)


class QueryRequest(BaseModel):
    q: str
    thread_id: Optional[str] = "default_user"


@app.get("/")
def home():
    return {"message": "Enterprise LangGraph RAG API is live."}


@app.get("/graph")
def get_graph_image():
    """Returns the Mermaid image of the agent's workflow."""
    try:
        png_bytes = rag_agent.get_graph().draw_mermaid_png()
        return Response(content=png_bytes, media_type="image/png")
    except Exception as e:
        return {"error": f"Could not generate graph image: {e}"}


@app.post("/query")
def query(request: QueryRequest):
    """Execute the LangGraph RAG flow with memory."""
    q = request.q
    thread_id = request.thread_id

    initial_state = {
        "messages": [{"role": "user", "content": q}],
        "current_query": q,
        "documents": [],
        "plan": ["Start"],
        "status": "Initializing Graph...",
    }

    langfuse_handler = CallbackHandler()
    config = {
        "configurable": {"thread_id": thread_id},
        "callbacks": [langfuse_handler],
    }

    try:
        with langfuse.start_as_current_observation(
            as_type="span",
            name="rag-query",
            input={"question": q, "thread_id": thread_id},
        ) as span:
            with propagate_attributes(
                trace_name="enterprise-rag-query",
                user_id=thread_id,
                session_id=thread_id,
                tags=["rag", "fastapi", "langgraph"],
                metadata={"endpoint": "/query"},
            ):
                rail_fired, rail_response = guard(q)
                if rail_fired:
                    logfire.info(
                        "Request handled by guardrails | thread={thread_id}",
                        thread_id=thread_id,
                    )
                    response_payload = {
                        "question": q,
                        "answer": rail_response,
                        "thought_process": ["Intent: Guardrails Fired", "Retrieval: Skipped"],
                        "status": "Handled by guardrails.",
                        "sources": [],
                    }
                    span.update(output=response_payload)
                    return response_payload

                final_output = rag_agent.invoke(initial_state, config=config)

            response_payload = {
                "question": q,
                "answer": final_output.get("final_answer"),
                "thought_process": final_output.get("plan"),
                "status": final_output.get("status"),
                "sources": final_output.get("documents", []),
            }
            span.update(output=response_payload)

        return response_payload
    except Exception as e:
        logfire.error("Backend execution failed: {error}", error=str(e))
        return JSONResponse(
            status_code=500,
            content={
                "question": q,
                "answer": "I apologize, but I encountered an internal error while processing your request. Please try again later.",
                "thought_process": ["Error encountered during execution."],
                "status": "error",
                "sources": [],
            },
        )
