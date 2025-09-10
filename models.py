"""
Pydantic models for request/response validation
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class ChatMessage(BaseModel):
    """Individual chat message model"""
    role: str = Field(..., description="Role of the message sender (user/assistant)")
    content: str = Field(..., description="Content of the message")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the message was created")


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., min_length=1, description="The message to send to the AI model")
    chat_id: Optional[str] = Field(None, description="Chat session ID (optional, will create new if not provided)")
    model: Optional[str] = Field(
        default="cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
        description="The AI model to use for the conversation"
    )
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty or whitespace only')
        return v.strip()


class ChatResponse(BaseModel):
    """Response model for successful chat completion"""
    response: str = Field(..., description="The AI model's response")
    chat_id: str = Field(..., description="Chat session ID")
    status: str = Field(default="success", description="Status of the request")
    model: str = Field(..., description="The model that generated the response")
    message_count: int = Field(..., description="Total messages in this conversation")


class ChatSession(BaseModel):
    """Chat session model for storing conversation history"""
    chat_id: str = Field(..., description="Unique chat session ID")
    messages: List[ChatMessage] = Field(default_factory=list, description="List of messages in the conversation")
    created_at: datetime = Field(default_factory=datetime.now, description="When the session was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="When the session was last updated")
    model: str = Field(..., description="AI model used for this session")


class ErrorResponse(BaseModel):
    """Response model for error cases"""
    error: str = Field(..., description="Error message")
    status: str = Field(default="error", description="Status of the request")
    code: int = Field(..., description="HTTP status code")