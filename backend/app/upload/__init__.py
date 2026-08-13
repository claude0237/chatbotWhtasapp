"""File Upload Controller"""
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
import logging
from app.auth.dependencies import get_current_active_user
from app.users.models import User
from app.logging_config import log_with_context

router = APIRouter(prefix="/upload", tags=["Upload"])
logger = logging.getLogger("app.upload")

UPLOAD_DIR = Path(__file__).parent.parent.parent / "static" / "uploads"
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
):
    """Upload an image and return its public URL"""
    log_with_context(
        logger,
        logging.INFO,
        "FILE_UPLOAD_STARTED",
        user_id=str(current_user.id),
        company_id=str(current_user.company_id),
        filename=file.filename,
        content_type=file.content_type
    )
    
    if file.content_type not in ALLOWED_TYPES:
        log_with_context(
            logger,
            logging.WARNING,
            "FILE_UPLOAD_VALIDATION_FAILED",
            user_id=str(current_user.id),
            company_id=str(current_user.company_id),
            filename=file.filename,
            content_type=file.content_type,
            reason="Invalid file type"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type non autorisé : {file.content_type}. Acceptés : JPEG, PNG, WebP, GIF",
        )

    contents = await file.read()
    if len(contents) > MAX_SIZE:
        log_with_context(
            logger,
            logging.WARNING,
            "FILE_UPLOAD_VALIDATION_FAILED",
            user_id=str(current_user.id),
            company_id=str(current_user.company_id),
            filename=file.filename,
            file_size=len(contents),
            reason="File too large"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fichier trop volumineux (max 5 Mo)",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename or "image.jpg").suffix.lower() or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / filename

    with open(dest, "wb") as f:
        f.write(contents)

    log_with_context(
        logger,
        logging.INFO,
        "FILE_UPLOAD_SUCCESS",
        user_id=str(current_user.id),
        company_id=str(current_user.company_id),
        filename=filename,
        file_size=len(contents)
    )
    
    return {"url": f"/static/uploads/{filename}"}
