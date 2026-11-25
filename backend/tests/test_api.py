
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db


@pytest.fixture
def client():
    # Create a separate temporary in-memory database for testing.
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def successful_reply(messages, failure_header=None):
    return {
        "reply": "Hello! I am Lyftr AI.",
        "resolution_source": "LIVE_INFERENCE",
        "model": "test-model",
        "latency_ms": 120,
        "input_tokens": 10,
        "output_tokens": 8,
        "key_id": "key_1",
        "fallback_attempts": 0,
    }


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["cache_enabled"] is True


def test_successful_chat(client, monkeypatch):
    monkeypatch.setattr(
        "app.main.generate_reply",
        successful_reply,
    )

    response = client.post(
        "/chat",
        json={
            "session_id": "test_session_001",
            "message": "Hello Lyftr AI",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["session_id"] == "test_session_001"
    assert data["reply"] == "Hello! I am Lyftr AI."
    assert data["metadata"]["resolution_source"] == "LIVE_INFERENCE"
    assert data["metadata"]["model"] == "test-model"
    assert data["metadata"]["latency_ms"] == 120
    assert data["metadata"]["input_tokens"] == 10
    assert data["metadata"]["output_tokens"] == 8


def test_invalid_chat_request(client):
    response = client.post(
        "/chat",
        json={
            "session_id": "",
            "message": "",
        },
    )

    assert response.status_code == 422


def test_unknown_session_returns_404(client):
    response = client.get(
        "/sessions/unknown_session/messages"
    )

    assert response.status_code == 404



def test_chat_history(client, monkeypatch):
    monkeypatch.setattr(
        "app.main.generate_reply",
        successful_reply,
    )

    first_response = client.post(
        "/chat",
        json={
            "session_id": "history_test",
            "message": "First message",
        },
    )

    print("First chat:", first_response.status_code, first_response.text)
    assert first_response.status_code == 200

    second_response = client.post(
        "/chat",
        json={
            "session_id": "history_test",
            "message": "Second message",
        },
    )

    print("Second chat:", second_response.status_code, second_response.text)
    assert second_response.status_code == 200

    response = client.get(
        "/sessions/history_test/messages"
    )

    print("History response:", response.status_code, response.text)
    assert response.status_code == 200

    messages = response.json()["messages"]

    assert len(messages) == 4
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "First message"
    assert messages[1]["role"] == "assistant"
    assert messages[2]["content"] == "Second message"


def test_all_providers_unavailable(client, monkeypatch):
    def failed_reply(messages, failure_header=None):
        raise RuntimeError("all providers unavailable")

    monkeypatch.setattr(
        "app.main.generate_reply",
        failed_reply,
    )

    response = client.post(
        "/chat",
        json={
            "session_id": "failed_test",
            "message": "Test failure",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "all providers unavailable"

    # Failed requests must not be saved in conversation history.
    history_response = client.get(
        "/sessions/failed_test/messages"
    )

    assert history_response.status_code == 404


def test_cache_metadata_is_returned(client, monkeypatch):
    def cached_reply(messages, failure_header=None):
        return {
            "reply": "Cached response",
            "resolution_source": "LLM_CACHE",
            "model": "test-model",
            "latency_ms": 5,
            "input_tokens": 10,
            "output_tokens": 8,
            "key_id": None,
            "fallback_attempts": 0,
        }

    monkeypatch.setattr(
        "app.main.generate_reply",
        cached_reply,
    )

    response = client.post(
        "/chat",
        json={
            "session_id": "cache_test",
            "message": "Repeat this question",
        },
    )

    assert response.status_code == 200

    metadata = response.json()["metadata"]

    assert metadata["resolution_source"] == "LLM_CACHE"
    assert metadata["key_id"] is None
    assert metadata["fallback_attempts"] == 0


def test_fallback_metadata_is_returned(client, monkeypatch):
    def fallback_reply(messages, failure_header=None):
        return {
            "reply": "Response from backup key",
            "resolution_source": "LIVE_INFERENCE",
            "model": "test-model",
            "latency_ms": 200,
            "input_tokens": 12,
            "output_tokens": 15,
            "key_id": "key_2",
            "fallback_attempts": 1,
        }

    monkeypatch.setattr(
        "app.main.generate_reply",
        fallback_reply,
    )

    response = client.post(
        "/chat",
        json={
            "session_id": "fallback_test",
            "message": "Test backup key",
        },
        headers={
            "X-Simulate-Failure": "key_1=429"
        },
    )

    assert response.status_code == 200

    metadata = response.json()["metadata"]

    assert metadata["key_id"] == "key_2"
    assert metadata["fallback_attempts"] == 1
    assert metadata["resolution_source"] == "LIVE_INFERENCE"
