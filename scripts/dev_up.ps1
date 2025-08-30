# Start FastAPI dev server
$env:PYTHONPATH = "$PSScriptRoot\.."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
