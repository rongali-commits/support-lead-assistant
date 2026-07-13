from __future__ import annotations

import re
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .retrieval import KnowledgeBase

PACKAGE_DIRECTORY = Path(__file__).parent
DATA_PATH = PACKAGE_DIRECTORY.parents[1] / "data" / "knowledge_base.json"
knowledge_base = KnowledgeBase.from_json(DATA_PATH)

app = FastAPI(
    title="Support & Lead Assistant",
    description="A deterministic, source-aware portfolio implementation with no external API calls.",
    version="1.0.0",
)


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)
    email: str | None = Field(default=None, max_length=200)


class Source(BaseModel):
    article_id: str
    title: str


class ChatResponse(BaseModel):
    answer: str
    intent: str
    lead_status: str
    sources: list[Source]


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(PACKAGE_DIRECTORY / "static" / "index.html")


@app.get("/health")
def health() -> dict[str, object]:
    return {"status": "ok", "knowledge_articles": len(knowledge_base.articles), "external_calls": 0}


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    results = knowledge_base.search(payload.question)
    intent = _classify_intent(payload.question)
    lead_status = _lead_status(intent, payload.email)
    if not results:
        fallback_intent = intent if intent != "general" else "unknown"
        return ChatResponse(
            answer=(
                "I could not find that in the approved knowledge base. Please share your email "
                "if you would like a person to follow up."
            ),
            intent=fallback_intent,
            lead_status=_lead_status(fallback_intent, payload.email),
            sources=[],
        )

    primary = results[0].article
    return ChatResponse(
        answer=primary.content,
        intent=intent,
        lead_status=lead_status,
        sources=[Source(article_id=item.article.article_id, title=item.article.title) for item in results],
    )


def _classify_intent(question: str) -> str:
    normalized = question.lower()
    routes = {
        "pricing": ("price", "pricing", "cost", "quote"),
        "booking": ("book", "call", "start", "available"),
        "documents": ("document", "pdf", "resume", "file"),
        "delivery": ("deliver", "deadline", "same-day", "timeline"),
    }
    for intent, keywords in routes.items():
        if any(keyword in normalized for keyword in keywords):
            return intent
    return "general"


def _lead_status(intent: str, email: str | None) -> str:
    valid_email = bool(email and re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))
    if valid_email and intent in {"pricing", "booking", "delivery"}:
        return "qualified_for_follow_up"
    if valid_email:
        return "follow_up_requested"
    return "not_captured"


def run() -> None:
    uvicorn.run("support_assistant.app:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    run()
