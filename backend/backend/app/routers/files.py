from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from typing import Annotated
import os
from urllib.parse import unquote

from app.deps import get_current_user
from app.models import User

router = APIRouter()

@router.get("/screenshot")
async def serve_screenshot(
    path: str = Query(..., description="Absolute path to screenshot file"),
    current_user: Annotated[User, Depends(get_current_user)] = None
):
    """Отдает скриншот по абсолютному пути (только для разработки)"""
    
    # Декодируем путь
    file_path = unquote(path)
    
    # Проверяем что файл существует
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Проверяем что это действительно изображение в temp папке
    if not file_path.startswith('/tmp/') and not file_path.startswith('/var/folders/'):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Проверяем расширение файла
    if not file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
        raise HTTPException(status_code=400, detail="Not an image file")
    
    return FileResponse(
        file_path, 
        media_type="image/png",
        filename=f"screenshot.png"
    )
