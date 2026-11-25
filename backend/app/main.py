
import json
from datetime import datetime, timezone

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app.models import Message
from app.schemas import ChatRequest
from app.config import LLM_API_KEYS, ALLOWED_ORIGINS
from app.llm_service import generate_reply


# Create database tables automatically
Base.metadata.create_all(bind=engine)


# Initialize FastAPI
app = FastAPI(
    title="Lyftr AI Chatbot",
    description="LLM Chatbot with Key Failover and Response Caching",
    version="1.0.0"
)


# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


DEFAULT_SYSTEM_PROMPT = "You are a helpful AI assistant."


# 1. Health endpoint
@app.get("/health")
def health():
    return {
        "status": "ok",
        "keys_configured": len(LLM_API_KEYS),
        "cache_enabled": True
    }


# 2. Chat endpoint
@app.post("/chat")
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    failure_header: str | None = Header(
        default=None,
        alias="X-Simulate-Failure"
    )
):
    # Get previous messages for this session
    previous_messages = (
        db.query(Message)
        .filter(Message.session_id == request.session_id)
        .order_by(Message.id.asc())
        .all()
    )

    # Build the complete LLM conversation
    system_prompt = (
        request.system_prompt.strip()
        if request.system_prompt and request.system_prompt.strip()
        else DEFAULT_SYSTEM_PROMPT
    )

    llm_messages = [
        {"role": "system", "content": system_prompt}
    ]

    for item in previous_messages:
        llm_messages.append({
            "role": item.role,
            "content": item.content
        })

    llm_messages.append({
        "role": "user",
        "content": request.message
    })

    # Generate the AI response
    try:
        result = generate_reply(
            messages=llm_messages,
            failure_header=failure_header
        )

    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="all providers unavailable"
        )

    # Save user message and assistant response only after success
    now = datetime.now(timezone.utc).isoformat()

    user_record = Message(
        session_id=request.session_id,
        role="user",
        content=request.message,
        metadata_json=None,
        created_at=now
    )

    assistant_metadata = {
        "resolution_source": result["resolution_source"],
        "model": result["model"],
        "latency_ms": result["latency_ms"],
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
        "key_id": result["key_id"],
        "fallback_attempts": result["fallback_attempts"]
    }

    assistant_record = Message(
        session_id=request.session_id,
        role="assistant",
        content=result["reply"],
        metadata_json=json.dumps(assistant_metadata),
        created_at=datetime.now(timezone.utc).isoformat()
    )

    try:
        db.add(user_record)
        db.add(assistant_record)
        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="could not save conversation"
        )

    return {
        "session_id": request.session_id,
        "reply": result["reply"],
        "metadata": assistant_metadata
    }


# 3. Retrieve all chat sessions
@app.get("/sessions")
def get_sessions(db: Session = Depends(get_db)):
    session_ids = db.query(Message.session_id).distinct().all()

    sessions = []

    for (session_id,) in session_ids:
        messages = (
            db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.id.asc())
            .all()
        )

        if not messages:
            continue

        first_user_message = next(
            (m.content for m in messages if m.role == "user"),
            "New conversation"
        )

        sessions.append({
            "session_id": session_id,
            "title": first_user_message[:45],
            "updated_at": messages[-1].created_at,
            "last_message_id": messages[-1].id
        })

    sessions.sort(
        key=lambda item: item["last_message_id"],
        reverse=True
    )

    return {
        "sessions": sessions
    }


# 4. Retrieve messages of a particular session
@app.get("/sessions/{session_id}/messages")
def get_messages(
    session_id: str,
    db: Session = Depends(get_db)
):
    messages = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.id.asc())
        .all()
    )

    # Return 404 if session does not exist
    if not messages:
        raise HTTPException(
            status_code=404,
            detail="session not found"
        )

    history = []

    for message in messages:
        item = {
            "role": message.role,
            "content": message.content
        }

        # Include metadata only for assistant messages
        if message.role == "assistant":
            try:
                item["metadata"] = json.loads(
                    message.metadata_json or "{}"
                )
            except json.JSONDecodeError:
                item["metadata"] = {}

        history.append(item)

    return {
        "session_id": session_id,
        "messages": history
    }
