from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from typing import Annotated
import os
from pathlib import Path

from app.deps import get_current_user
from app.models import User

router = APIRouter()

# Временное хранилище путей к скриншотам
screenshot_storage = {}

@router.post("/store")
async def store_screenshot_path(
    task_id: str,
    screenshot_path: str,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Сохраняет путь к скриншоту для задачи"""
    screenshot_storage[task_id] = screenshot_path
    return {"status": "stored", "task_id": task_id}

@router.get("/{task_id}")
async def get_screenshot(
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Возвращает скриншот по task_id"""
    screenshot_path = screenshot_storage.get(task_id)
    
    if not screenshot_path:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    
    if not os.path.exists(screenshot_path):
        raise HTTPException(status_code=404, detail="Screenshot file not found")
    
    return FileResponse(
        screenshot_path, 
        media_type="image/png",
        filename=f"screenshot_{task_id}.png"
    )
