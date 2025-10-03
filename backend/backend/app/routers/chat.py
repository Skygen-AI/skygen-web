from __future__ import annotations
from pydantic import BaseModel

import uuid
import re
from typing import Annotated, List
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.deps import get_current_user
from app.models import User, ChatSession, ChatMessage, Device
from app.schemas import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatSessionWithMessages,
)
from app.routing import publish_task_envelope
from app.security import sign_message_hmac

router = APIRouter()


@router.post("/sessions", response_model=ChatSessionResponse, status_code=201)
async def create_chat_session(
    payload: ChatSessionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChatSessionResponse:
    """Создание новой чат-сессии"""

    # Проверяем, что устройство принадлежит пользователю, если указано
    if payload.device_id:
        device_result = await db.execute(
            select(Device).where(
                Device.id == payload.device_id,
                Device.user_id == current_user.id
            )
        )
        device = device_result.scalar_one_or_none()
        if not device:
            # Если устройство не найдено, логируем это но не прерываем создание сессии
            # Это может произойти если устройство зарегистрировано но еще не синхронизировано
            from loguru import logger
            logger.warning(
                f"Device {payload.device_id} not found for user {current_user.id}, creating session without device_id")
            payload.device_id = None

    session = ChatSession(
        user_id=current_user.id,
        device_id=payload.device_id,
        title=payload.title,
        meta_data=payload.metadata,
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    return ChatSessionResponse(
        id=session.id,
        user_id=session.user_id,
        device_id=session.device_id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        is_active=session.is_active,
        metadata=session.meta_data,
        message_count=0,
    )


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_chat_sessions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    active_only: bool = Query(default=True),
) -> List[ChatSessionResponse]:
    """Получение списка чат-сессий пользователя"""

    query = select(ChatSession, func.count(ChatMessage.id).label("message_count")).outerjoin(
        ChatMessage, ChatSession.id == ChatMessage.session_id
    ).where(ChatSession.user_id == current_user.id)

    if active_only:
        query = query.where(ChatSession.is_active == True)

    query = query.group_by(ChatSession.id).order_by(
        desc(ChatSession.updated_at)
    ).limit(limit).offset(offset)

    result = await db.execute(query)
    sessions_with_counts = result.all()

    return [
        ChatSessionResponse(
            id=session.id,
            user_id=session.user_id,
            device_id=session.device_id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            is_active=session.is_active,
            metadata=session.meta_data,
            message_count=message_count,
        )
        for session, message_count in sessions_with_counts
    ]


@router.get("/sessions/{session_id}", response_model=ChatSessionWithMessages)
async def get_chat_session(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChatSessionWithMessages:
    """Получение чат-сессии с сообщениями"""

    result = await db.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    # Сортируем сообщения по времени создания
    messages = sorted(session.messages, key=lambda m: m.created_at)

    return ChatSessionWithMessages(
        id=session.id,
        user_id=session.user_id,
        device_id=session.device_id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        is_active=session.is_active,
        metadata=session.meta_data,
        messages=[
            ChatMessageResponse(
                id=msg.id,
                session_id=msg.session_id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at,
                metadata=msg.meta_data,
                task_id=msg.task_id,
            )
            for msg in messages
        ],
    )


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse, status_code=201)
async def create_message(
    session_id: uuid.UUID,
    payload: ChatMessageCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChatMessageResponse:
    """Добавление сообщения в чат"""

    # Проверяем, что сессия принадлежит пользователю
    session_result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    if not session.is_active:
        raise HTTPException(
            status_code=400, detail="Chat session is not active")

    message = ChatMessage(
        session_id=session_id,
        role=payload.role,
        content=payload.content,
        meta_data=payload.metadata,
    )

    db.add(message)

    # Обновляем время последнего обновления сессии
    session.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(message)

    return ChatMessageResponse(
        id=message.id,
        session_id=message.session_id,
        role=message.role,
        content=message.content,
        created_at=message.created_at,
        metadata=message.meta_data,
        task_id=message.task_id,
    )


@router.put("/sessions/{session_id}")
async def update_chat_session(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    title: str | None = None,
    is_active: bool | None = None,
    metadata: dict | None = None,
) -> ChatSessionResponse:
    """Обновление чат-сессии"""

    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    if title is not None:
        session.title = title
    if is_active is not None:
        session.is_active = is_active
    if metadata is not None:
        session.meta_data = metadata

    session.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(session)

    # Получаем количество сообщений
    message_count_result = await db.execute(
        select(func.count(ChatMessage.id)).where(
            ChatMessage.session_id == session_id)
    )
    message_count = message_count_result.scalar() or 0

    return ChatSessionResponse(
        id=session.id,
        user_id=session.user_id,
        device_id=session.device_id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        is_active=session.is_active,
        metadata=session.meta_data,
        message_count=message_count,
    )


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Удаление чат-сессии"""

    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    await db.delete(session)
    await db.commit()

    return {"message": "Chat session deleted successfully"}


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def list_messages(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
) -> List[ChatMessageResponse]:
    """Получение сообщений чата с пагинацией"""

    # Проверяем, что сессия принадлежит пользователю
    session_result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    # Получаем сообщения
    messages_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .limit(limit)
        .offset(offset)
    )
    messages = messages_result.scalars().all()

    return [
        ChatMessageResponse(
            id=msg.id,
            session_id=msg.session_id,
            role=msg.role,
            content=msg.content,
            created_at=msg.created_at,
            metadata=msg.meta_data,
            task_id=msg.task_id,
        )
        for msg in messages
    ]


class AgentChatRequest(BaseModel):
    message: str
    session_id: uuid.UUID | None = None
    device_id: uuid.UUID | None = None


@router.post("/agent")
async def chat_with_agent(
    request: AgentChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """AI агент для обработки chat команд и выполнения desktop действий"""

    # Создаем сообщение пользователя
    user_message = ChatMessage(
        session_id=request.session_id,
        role="user",
        content=request.message,
    )

    if request.session_id:
        db.add(user_message)
        await db.commit()
        await db.refresh(user_message)

    # Анализируем сообщение на команды
    response_content = ""
    task_created = False
    task_id = None
    screenshot_url = None

    message_lower = request.message.lower().strip()

    # Команда скриншот
    if "скриншот" in message_lower or "screenshot" in message_lower:
        if request.device_id:
            # Проверяем, что устройство существует и принадлежит пользователю
            from app.models import Task
            device_result = await db.execute(
                select(Device).where(
                    Device.id == request.device_id,
                    Device.user_id == current_user.id
                )
            )
            device = device_result.scalar_one_or_none()

            if not device:
                response_content = "⚠️ Устройство не найдено или не принадлежит вам"
            else:
                # Создаем задачу для скриншота
                task = Task(
                    id=str(uuid.uuid4()),
                    user_id=current_user.id,
                    device_id=request.device_id,
                    title="Скриншот экрана",
                    description="Создание скриншота рабочего стола",
                    status="queued",
                    payload={
                        "actions": [
                            {
                                "action_id": str(uuid.uuid4()),
                                "type": "screenshot",
                                "action_type": "screenshot",
                                "description": "Делаю скриншот экрана"
                            }
                        ]
                    }
                )
                db.add(task)
                await db.commit()
                await db.refresh(task)

                # Отправляем задачу на устройство
                envelope = {
                    "type": "task.exec",
                    "task_id": str(task.id),
                    "issued_at": datetime.now(timezone.utc).isoformat(),
                    "actions": task.payload.get("actions", []),
                }
                envelope["signature"] = sign_message_hmac(envelope)
                await publish_task_envelope(str(request.device_id), envelope)

                task_created = True
                task_id = str(task.id)
                response_content = "📸 Делаю скриншот экрана..."
                
                # Ждем немного для обработки задачи и пытаемся получить screenshot URL
                import asyncio
                await asyncio.sleep(3)  # Даем время агенту обработать задачу
                
                # Проверяем результат задачи
                await db.refresh(task)
                if task.status == "completed" and task.result:
                    # Извлекаем screenshot_path из результата
                    results = task.result.get("results", [])
                    for result in results:
                        if result.get("action_type") == "screenshot" and result.get("result"):
                            screenshot_path = result["result"].get("screenshot_path")
                            if screenshot_path and screenshot_path.startswith("http"):
                                screenshot_url = screenshot_path
                                response_content = f"✅ Скриншот готов!\n\n![Screenshot]({screenshot_url})"
                                break
                    
                    if not screenshot_url:
                        response_content = "✅ Скриншот выполнен, но изображение недоступно"

        else:
            response_content = "⚠️ Для скриншота нужно подключить устройство"

    # Команда движения курсора
    elif "передвинь" in message_lower or "move" in message_lower:
        # Извлекаем координаты
        coords_match = re.search(r"(\d+)[,\s]+(\d+)", request.message)
        if coords_match and request.device_id:
            # Проверяем, что устройство существует и принадлежит пользователю
            device_result = await db.execute(
                select(Device).where(
                    Device.id == request.device_id,
                    Device.user_id == current_user.id
                )
            )
            device = device_result.scalar_one_or_none()

            if not device:
                response_content = "⚠️ Устройство не найдено или не принадлежит вам"
            else:
                x, y = int(coords_match.group(1)), int(coords_match.group(2))

                from app.models import Task
                task = Task(
                    id=str(uuid.uuid4()),
                    user_id=current_user.id,
                    device_id=request.device_id,
                    title="Перемещение курсора",
                    description=f"Перемещение курсора в координаты ({x}, {y})",
                    status="queued",
                    payload={
                        "actions": [
                            {
                                "action_id": str(uuid.uuid4()),
                                "action_type": "move_cursor",
                                "x": x,
                                "y": y,
                                "description": f"Перемещаю курсор в координаты ({x}, {y})"
                            }
                        ]
                    }
                )
                db.add(task)
                await db.commit()
                await db.refresh(task)

                # Отправляем задачу на устройство
                envelope = {
                    "type": "task.exec",
                    "task_id": str(task.id),
                    "issued_at": datetime.now(timezone.utc).isoformat(),
                    "actions": task.payload.get("actions", []),
                }
                envelope["signature"] = sign_message_hmac(envelope)
                await publish_task_envelope(str(request.device_id), envelope)

                task_created = True
                task_id = str(task.id)
                response_content = f"🖱️ Перемещаю курсор в координаты ({x}, {y})"

        elif coords_match:
            response_content = "⚠️ Для движения курсора нужно подключить устройство"
        else:
            response_content = "❓ Не могу найти координаты. Используйте формат: передвинь 100, 200"

    else:
        response_content = "🤖 Привет! Я умею делать скриншоты и двигать курсор. Попробуйте команды:\n• скриншот\n• передвинь 100, 200"

    # Создаем ответное сообщение агента
    agent_message = ChatMessage(
        session_id=request.session_id,
        role="assistant",
        content=response_content,
        task_id=task_id
    )

    if request.session_id:
        db.add(agent_message)
        await db.commit()
        await db.refresh(agent_message)

    return {
        "message": {
            "id": str(user_message.id) if request.session_id else None,
            "session_id": str(request.session_id) if request.session_id else None,
            "role": "user",
            "content": request.message,
            "created_at": user_message.created_at.isoformat() if request.session_id else datetime.utcnow().isoformat(),
            "task_id": None,
        },
        "assistant_message": {
            "id": str(agent_message.id) if request.session_id else None,
            "session_id": str(request.session_id) if request.session_id else None,
            "role": "assistant",
            "content": response_content,
            "created_at": agent_message.created_at.isoformat() if request.session_id else datetime.utcnow().isoformat(),
            "task_id": task_id,
        },
        "task_created": task_created,
        "task_id": task_id,
        "screenshot_url": screenshot_url,
    }
