from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
import os
from uuid import uuid4

router = APIRouter()

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../uploads'))
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post('/upload')
async def upload_file(request: Request, file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail='Only image uploads are allowed')
    ext = os.path.splitext(file.filename)[1].lower()
    name = f"{uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, name)
    with open(path, 'wb') as f:
        f.write(await file.read())
    # Return absolute URL that the frontend can access (served at /uploads)
    base = str(request.base_url).rstrip('/')
    return JSONResponse({ 'url': f"{base}/uploads/{name}" })
