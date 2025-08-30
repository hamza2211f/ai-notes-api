# Register, login, create a note, run summarize
$base = "http://127.0.0.1:8000"

# Register
$reg = Invoke-RestMethod -Method POST -Uri "$base/register" -ContentType "application/json" -Body (@{email="demo@example.com"; password="secret123"} | ConvertTo-Json)

# Login
$login = Invoke-RestMethod -Method POST -Uri "$base/login" -ContentType "application/x-www-form-urlencoded" -Body "username=demo@example.com&password=secret123"
$token = $login.access_token
$headers = @{ Authorization = "Bearer $token" }

# Create a note
$note = Invoke-RestMethod -Method POST -Uri "$base/notes" -Headers $headers -ContentType "application/json" -Body (@{title="Hello"; content="FastAPI with HF pipelines is awesome"} | ConvertTo-Json)

# Summarize async
$job = Invoke-RestMethod -Method POST -Uri "$base/notes/$($note.id)/summarize-async" -Headers $headers

Write-Host "Token:" $token
Write-Host "Note:" ($note | ConvertTo-Json)
Write-Host "Job:" ($job | ConvertTo-Json)
