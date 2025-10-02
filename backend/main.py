from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api_v1.api import api_router
from app.core.config import settings
from fastapi.staticfiles import StaticFiles
from app.api.api_v1.endpoints import files as files_router
import os

app = FastAPI(
    title="Medical Exam Preparation API",
    description="API for medical exam preparation platform",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "http://localhost:5173"],  # Vue.js dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(files_router.router, prefix=f"{settings.API_V1_STR}/files", tags=["files"])

# Static serving for uploads
UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'app/uploads'))
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount('/uploads', StaticFiles(directory=UPLOAD_DIR), name='uploads')

@app.get("/")
def read_root():
    return {"message": "Medical Exam Preparation API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
