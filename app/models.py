from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from .database import Base
import enum

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    notes = relationship("Note", back_populates="owner")

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    summary = Column(Text, nullable=True)
    summary_model = Column(String, nullable=True)
    summarized_at = Column(TIMESTAMP(timezone=True), nullable=True)
    sentiment = Column(String, nullable=True)
    sentiment_model = Column(String, nullable=True)
    analyzed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    owner = relationship("User", back_populates="notes")

class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, nullable=False)
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    task = Column(String, nullable=False)
    status = Column(SAEnum(JobStatus), nullable=False, server_default=text("'PENDING'"))
    detail = Column(String, nullable=True) 
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))



