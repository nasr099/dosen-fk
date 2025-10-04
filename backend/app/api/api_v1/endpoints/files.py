from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
import os
from uuid import uuid4
import boto3
from botocore.client import Config
from app.core.config import settings

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


@router.post('/presign')
async def presign_upload(request: Request):
    body = await request.json()
    filename = (body.get('filename') or '').strip()
    content_type = (body.get('content_type') or 'application/octet-stream').strip()
    if not filename:
        raise HTTPException(status_code=400, detail='filename is required')
    # Read from pydantic settings (loaded from .env)
    DO_BUCKET = settings.DO_SPACES_BUCKET
    DO_REGION = settings.DO_SPACES_REGION or 'sgp1'
    DO_ENDPOINT = settings.DO_SPACES_ENDPOINT or f'https://{DO_REGION}.digitaloceanspaces.com'
    DO_KEY = settings.DO_SPACES_KEY
    DO_SECRET = settings.DO_SPACES_SECRET
    PUBLIC_CDN_BASE = settings.PUBLIC_CDN_BASE
    if not all([DO_BUCKET, DO_KEY, DO_SECRET, DO_ENDPOINT]):
        raise HTTPException(status_code=500, detail='Spaces is not configured on the server (missing env)')

    key = f"uploads/{uuid4().hex}-{filename}"

    s3 = boto3.client(
        's3',
        region_name=DO_REGION,
        endpoint_url=DO_ENDPOINT,
        aws_access_key_id=DO_KEY,
        aws_secret_access_key=DO_SECRET,
        config=Config(signature_version='s3v4')
    )

    params = {
        'Bucket': DO_BUCKET,
        'Key': key,
        'ContentType': content_type,
        'ACL': 'public-read',
        'CacheControl': 'public, max-age=31536000, immutable'
    }
    # Generate presigned PUT URL (valid for 60s)
    upload_url = s3.generate_presigned_url(
        ClientMethod='put_object',
        Params=params,
        ExpiresIn=60
    )

    public_base = PUBLIC_CDN_BASE or f"https://{DO_BUCKET}.{DO_REGION}.digitaloceanspaces.com"
    public_url = f"{public_base}/{key}"

    return JSONResponse({
        'upload_url': upload_url,
        'public_url': public_url,
        'key': key
    })
