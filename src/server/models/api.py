# src/server/models/api.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

from flask import current_app, request, jsonify
from src.server.api.llm_adapter import LLMAdapter




# Request Models (Input)
class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, example="john_doe")
    native_language: str = Field(..., min_length=2, max_length=5, example="de")

class SentenceCreateRequest(BaseModel):
    original_text: str = Field(..., min_length=1, max_length=200, example="Ich lerne Deutsch")
    category: Optional[str] = Field(None, max_length=50, example="Lernen")
    user_id: int = Field(..., gt=0, example=1)

class SessionCreateRequest(BaseModel):
    sentence_id: int = Field(..., gt=0, example=1)
    input_data: dict = Field(..., example={"translations": {"en": "I learn German"}})
    score: Optional[float] = Field(None, ge=0.0, le=1.0, example=0.8)

class LearningAttemptRequest(BaseModel):
    sentence_id: int = Field(..., gt=0, example=1)
    user_answer: str = Field(..., min_length=1, example="I learn German")

# Response Models (Output)
class UserResponse(BaseModel):
    id: int
    username: str
    native_language: str
    created_at: datetime

    class Config:
        from_attributes = True

class UserCreateResponse(BaseModel):
    success: bool
    message: str
    user: UserResponse  

class SentenceResponse(BaseModel):
    id: int
    user_id: int
    original_text: str
    language_code: str
    category: Optional[str]
    score: float
    last_review: Optional[datetime]
    next_review: Optional[datetime]
    review_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class SentenceCreateResponse(BaseModel):
    success: bool
    message: str
    sentence: SentenceResponse

class SessionResponse(BaseModel):
    id: int
    user_id: int
    sentence_id: int
    input: Optional[dict]
    score: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True

class SentenceWithProgressResponse(BaseModel):
    id: int
    user_id: int
    original_text: str
    language_code: str
    category: Optional[str]
    score: float
    last_review: Optional[datetime]
    next_review: Optional[datetime]
    review_count: int
    created_at: datetime

    class Config:
        from_attributes = True

# Additional Models
class SupportedLanguageResponse(BaseModel):
    code: str
    name: str

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None