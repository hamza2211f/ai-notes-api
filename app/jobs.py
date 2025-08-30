from fastapi import BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from . import models, database, oauth2
from .summarizer import summarize_text
from .sentiment import analyze_sentiment

def run_job(job_id: int, task: str):
  
    db: Session = next(database.get_db())  

    try:
        job = db.query(models.Job).filter(models.Job.id == job_id).first()
        if not job:
            return 

        job.status = models.JobStatus.RUNNING
        job.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(job)

        note = db.query(models.Note).filter(models.Note.id == job.note_id).first()
        if not note:
            job.status = models.JobStatus.FAILED
            job.detail = "Note not found"
            job.updated_at = datetime.utcnow()
            db.commit()
            return

        if task == "summarize":
            if not (note.content or "").strip():
                raise ValueError("Cannot summarize empty text")

            summary, model_id = summarize_text(note.content)
            note.summary = summary
            note.summary_model = model_id
            note.summarized_at = datetime.utcnow()

        elif task == "sentiment":
            if not (note.content or "").strip():
                raise ValueError("Cannot analyze empty text")

            label, model_id = analyze_sentiment(note.content)
            note.sentiment = label
            note.sentiment_model = model_id
            note.analyzed_at = datetime.utcnow()

        else:
            raise ValueError(f"Unknown task: {task}")

        job.status = models.JobStatus.SUCCEEDED
        job.detail = None
        job.updated_at = datetime.utcnow()

        db.add_all([note, job])
        db.commit()

    except ValueError as e:
        job = db.query(models.Job).filter(models.Job.id == job_id).first()
        if job:
            job.status = models.JobStatus.FAILED
            job.detail = str(e)
            job.updated_at = datetime.utcnow()
            db.commit()
    except Exception as e:
        job = db.query(models.Job).filter(models.Job.id == job_id).first()
        if job:
            job.status = models.JobStatus.FAILED
            job.detail = "backend error"
            job.updated_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()
