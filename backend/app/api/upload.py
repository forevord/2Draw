"""Image upload endpoint.

PS-10: Accepts JPEG/PNG images (≤20 MB), saves to a local staging directory,
and returns an upload_id that downstream pipeline endpoints reference.
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel

router = APIRouter(tags=["upload"])

_UPLOAD_DIR = Path("/tmp/paintsnap/uploads")
_MAX_SIZE = 20 * 1024 * 1024  # 20 MB
_ALLOWED_TYPES = {"image/jpeg", "image/png"}


class UploadResponse(BaseModel):
    upload_id: str
    filename: str
    size: int


@router.post("/upload", response_model=UploadResponse)
async def upload_image(file: UploadFile) -> UploadResponse:
    """Accept an image file, save to disk, and return an upload_id."""
    if file.content_type not in _ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Use JPEG or PNG.",
        )

    data = await file.read()
    if len(data) > _MAX_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {len(data)} bytes. Max is 20 MB.",
        )

    upload_id = uuid4().hex
    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = _UPLOAD_DIR / upload_id
    dest.write_bytes(data)

    return UploadResponse(
        upload_id=upload_id,
        filename=file.filename or "unknown",
        size=len(data),
    )
