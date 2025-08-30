from pydantic import BaseModel, EmailStr, conint
from datetime import datetime
from typing import Optional, Literal

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True

class NoteCreate(BaseModel):
    title: str
    content: str

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class NoteOut(BaseModel):
    id: int
    title: str
    content: str
    owner_id: int
    created_at: datetime

    summary: Optional[str] = None
    summary_model: Optional[str] = None
    summarized_at: Optional[datetime] = None

    sentiment: Optional[str] = None
    sentiment_model: Optional[str] = None
    analyzed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[str] = None

class JobOut(BaseModel):
    id: int
    note_id: int
    task: Literal["summarize", "sentiment"]
    status: Literal["PENDING", "RUNNING", "SUCCEEDED", "FAILED"]
    detail: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True