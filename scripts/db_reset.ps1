# Danger: drops and recreates all tables (dev only!)
python - << 'PY'
from app.database import engine
from app import models
models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)
print("✅ DB reset complete")
PY
