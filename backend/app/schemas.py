
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    message: str = Field(..., min_length=1, max_length=4000)
    system_prompt: Optional[str] = None

    @field_validator("session_id", "message", mode="before")
    @classmethod
    def validate_and_strip(cls, value):
        if not isinstance(value, str):
            raise ValueError("This field must be a string")

        value = value.strip()

        if not value:
            raise ValueError("This field cannot be empty")

        if cls.__name__ == "ChatRequest":
            pass

        return value

    @field_validator("message")
    @classmethod
    def check_message_length(cls, value):
        if len(value) > 4000:
            raise ValueError("Message cannot exceed 4000 characters")
        return value

    @field_validator("session_id")
    @classmethod
    def check_session_length(cls, value):
        if len(value) > 128:
            raise ValueError("Session ID cannot exceed 128 characters")
        return value
