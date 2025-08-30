from fastapi import FastAPI, status, HTTPException, Depends, Response, BackgroundTasks
from sqlalchemy.orm import Session
from .config import settings
from . import schemas, database, models, utils, oauth2
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from typing import List, Optional
from .summarizer import summarize_text
from datetime import datetime, timezone
from .sentiment import analyze_sentiment
from .jobs import run_job
app = FastAPI()

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/register",status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    hashed_password = utils.hash(user.password)
    user.password = hashed_password
    new_user = models.User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login", response_model=schemas.Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == user_credentials.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")
    if not utils.verify(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")
    access_token = oauth2.create_access_token(data={"user_id": user.id})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.get("/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(oauth2.get_current_user)):
    return current_user

@app.post("/notes", response_model=schemas.NoteOut)
def create_note(note: schemas.NoteCreate,db:Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    new_note = models.Note(**note.dict())
    new_note.owner_id = current_user.id
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return new_note

@app.get("/notes", response_model=List[schemas.NoteOut])
def get_notes(current_user: models.User = Depends(oauth2.get_current_user),
              db: Session = Depends(database.get_db),
              limit: int = 10, skip: int = 0, search: Optional[str] = ""):
    
    notes = db.query(models.Note).filter(models.Note.owner_id == current_user.id).filter(models.Note.title.contains(search)).limit(limit).offset(skip).all()
    if not notes:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="current user does not have notes") 
    return  notes

@app.get("/notes/{id}", response_model=schemas.NoteOut)
def get_specific_notes(id: int, current_user: models.User = Depends(oauth2.get_current_user),
              db: Session = Depends(database.get_db)):
    note = db.query(models.Note).filter(models.Note.id == id, models.Note.owner_id == current_user.id).first()
    
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="current user does not have the specified note")
    
    return  note

@app.put("/notes/{id}", response_model=schemas.NoteOut)
def update_note(
    id: int,
    updated_note: schemas.NoteUpdate,
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(database.get_db),
):
    note_query = db.query(models.Note).filter(
        models.Note.id == id,
        models.Note.owner_id == current_user.id
    )
    note = note_query.first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    data = updated_note.model_dump(exclude_unset=True, exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")

    note_query.update(data, synchronize_session=False) # type: ignore
    db.commit()
    return note_query.first()

@app.delete("/delete/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(id: int, current_user: models.User = Depends(oauth2.get_current_user),
                db: Session = Depends(database.get_db)):
    
    note_query = db.query(models.Note).filter(models.Note.id == id, models.Note.owner_id == current_user.id)
    note  = note_query.first()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    note_query.delete(synchronize_session=False)
    db.commit()
    return



@app.post("/notes/{id}/summarize", response_model=schemas.NoteOut)
def summarize_note(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):

    note = (
        db.query(models.Note)
        .filter(models.Note.id == id, models.Note.owner_id == current_user.id)
        .first()
    )
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    if not (note.content or "").strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Note content is empty")

    if note.summarized_at and (note.updated_at and note.summarized_at >= note.updated_at):
        return note

    try:
        summary, model_id = summarize_text(note.content)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Summarizer backend error")

    note.summary = summary
    note.summary_model = model_id
    note.summarized_at = datetime.utcnow()
    note.updated_at = datetime.now(timezone.utc)

    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@app.post("/notes/{id}/sentiment", response_model=schemas.NoteOut)
def analyze_note(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    note = (
        db.query(models.Note)
          .filter(models.Note.id == id, models.Note.owner_id == current_user.id)  # type: ignore
          .first()
    )
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no note to be analyzed")

    if not (note.content or "").strip():
        raise HTTPException(status_code=400, detail="content is empty")

    # Cache: only re-run if note changed since last analysis
    if note.analyzed_at and (note.updated_at is None or note.analyzed_at >= note.updated_at):
        return note

    try:
        sentiment, model_id = analyze_sentiment(note.content)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="analyzer backend error")

    note.sentiment = sentiment
    note.sentiment_model = model_id
    note.analyzed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(note)
    return note

    
@app.post("/notes/{id}/summarize-async", response_model=schemas.JobOut, status_code=202)
def summarize_async(
    id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    # authorize / own note
    note = db.query(models.Note).filter(
        models.Note.id == id,
        models.Note.owner_id == current_user.id
    ).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="note not found")

    # create job
    job = models.Job(note_id=id, task="summarize", status=models.JobStatus.PENDING)
    db.add(job)
    db.commit()
    db.refresh(job)

    # schedule background work
    background_tasks.add_task(run_job, job.id, "summarize")

    return job


@app.post("/notes/{id}/sentiment-async", response_model=schemas.JobOut, status_code=202)
def sentiment_async(
    id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    note = db.query(models.Note).filter(
        models.Note.id == id,
        models.Note.owner_id == current_user.id
    ).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="note not found")

    job = models.Job(note_id=id, task="sentiment", status=models.JobStatus.PENDING)
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(run_job, job.id, "sentiment")

    return job


@app.get("/jobs/{job_id}", response_model=schemas.JobOut)
def get_job(job_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="job not found")

    # Optional: enforce that the job belongs to a note owned by current_user
    note = db.query(models.Note).filter(models.Note.id == job.note_id).first()
    if not note or note.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="forbidden")

    return job
