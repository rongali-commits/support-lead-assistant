from fastapi.testclient import TestClient

from support_assistant.app import app

client = TestClient(app)


def test_health_reports_local_demo_boundaries() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "knowledge_articles": 4, "external_calls": 0}


def test_chat_returns_an_approved_answer_and_sources() -> None:
    response = client.post(
        "/api/chat",
        json={"question": "Can you automate PDF documents and files?", "email": None},
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["intent"] == "documents"
    assert payload["sources"][0]["article_id"] == "documents"
    assert "Sensitive files" in payload["answer"]


def test_high_intent_question_with_email_is_qualified() -> None:
    response = client.post(
        "/api/chat",
        json={"question": "What would this cost?", "email": "buyer@example.com"},
    )
    assert response.json()["lead_status"] == "qualified_for_follow_up"


def test_unknown_question_uses_safe_fallback() -> None:
    response = client.post("/api/chat", json={"question": "Do you sell bicycles?"})
    payload = response.json()
    assert payload["intent"] == "unknown"
    assert payload["sources"] == []

