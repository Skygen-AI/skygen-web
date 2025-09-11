from __future__ import annotations

import uuid
import json
from typing import Annotated
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models import User, ChatSession, ChatMessage, Device, Task
from app.schemas import AgentChatRequest, AgentChatResponse, ChatMessageResponse
from app.clients import publish_event
from loguru import logger

router = APIRouter()

# Простой AI агент для демонстрации


class SimpleAgent:
    """Простой AI агент для обработки сообщений и создания задач"""

    @staticmethod
    def should_create_task(message: str) -> bool:
        """Определяет, нужно ли создавать задачу из сообщения"""
        task_keywords = [
            "screenshot", "скриншот", "скрин", "снимок экрана",
            "click", "кликни", "нажми", "клик",
            "type", "напечатай", "введи", "набери",
            "open", "открой", "запусти",
            "close", "закрой",
            "find", "найди", "поиск",
            "scroll", "прокрути", "скролл",
            "task", "задача", "выполни", "сделай"
        ]

        message_lower = message.lower()
        return any(keyword in message_lower for keyword in task_keywords)

    @staticmethod
    def parse_task_from_message(message: str, device_id: uuid.UUID) -> dict:
        """Парсит сообщение и создает структуру задачи"""
        message_lower = message.lower()

        # Определяем тип действия
        if any(word in message_lower for word in ["screenshot", "скриншот", "скрин", "снимок"]):
            action_type = "screenshot"
            actions = [{
                "action_id": str(uuid.uuid4()),
                "type": "screenshot",
                "params": {}
            }]
            title = "Take Screenshot"
            description = f"Taking screenshot as requested: {message}"

        elif any(word in message_lower for word in ["click", "кликни", "нажми"]):
            action_type = "click"
            actions = [{
                "action_id": str(uuid.uuid4()),
                "type": "execute_action",
                "params": {
                    "action": {
                        "action_type": "CLICK",
                        "x": 500,  # Default position
                        "y": 300
                    }
                }
            }]
            title = "Click Action"
            description = f"Performing click action: {message}"

        elif any(word in message_lower for word in ["type", "напечатай", "введи"]):
            # Пытаемся извлечь текст для ввода
            text_to_type = message
            if "напечатай" in message_lower:
                text_to_type = message.split("напечатай", 1)[-1].strip()
            elif "введи" in message_lower:
                text_to_type = message.split("введи", 1)[-1].strip()
            elif "type" in message_lower:
                text_to_type = message.split("type", 1)[-1].strip()

            action_type = "type_text"
            actions = [{
                "action_id": str(uuid.uuid4()),
                "type": "type_text",
                "params": {
                    "text": text_to_type
                }
            }]
            title = "Type Text"
            description = f"Typing text: {text_to_type}"

        else:
            # Общая задача
            action_type = "general"
            actions = [{
                "action_id": str(uuid.uuid4()),
                "type": "screenshot",
                "params": {}
            }]
            title = "General Task"
            description = f"Processing request: {message}"

        return {
            "title": title,
            "description": description,
            "actions": actions,
            "metadata": {
                "source": "chat",
                "original_message": message,
                "action_type": action_type
            }
        }

    @staticmethod
    def generate_response(message: str, task_created: bool = False, task_id: str = None) -> str:
        """Генерирует ответ агента"""
        if task_created:
            return f"Понял! Я создал задачу для выполнения вашего запроса. Задача #{task_id} будет выполнена на подключенном устройстве."

        message_lower = message.lower()

        if any(word in message_lower for word in ["привет", "hello", "hi"]):
            return "Привет! Я ваш AI агент для автоматизации задач. Я могу помочь вам с управлением устройством, созданием скриншотов, кликами, вводом текста и многим другим. Просто опишите, что вам нужно сделать!"

        elif any(word in message_lower for word in ["помощь", "help", "что ты умеешь"]):
            return """Я умею выполнять различные задачи на вашем устройстве:

🖥️ **Скриншоты**: "Сделай скриншот", "screenshot"
🖱️ **Клики**: "Кликни на кнопку", "click at position"  
⌨️ **Ввод текста**: "Напечатай 'Hello World'", "type some text"
🪟 **Управление окнами**: "Открой приложение", "закрой окно"
🔍 **Поиск**: "Найди файл", "find element"

Просто опишите, что вам нужно, и я создам соответствующую задачу!"""

        elif any(word in message_lower for word in ["спасибо", "thanks", "thank you"]):
            return "Пожалуйста! Всегда рад помочь. Если нужно что-то еще - просто напишите!"

        else:
            return "Я обработал ваше сообщение. Если это была команда для выполнения действий на устройстве, я создам соответствующую задачу. Иначе, уточните, пожалуйста, что именно вы хотите сделать."


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(
    payload: AgentChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AgentChatResponse:
    """Основной endpoint для общения с AI агентом"""

    session_id = payload.session_id
    device_id = payload.device_id

    # Если сессия не указана, создаем новую
    if not session_id:
        session = ChatSession(
            user_id=current_user.id,
            device_id=device_id,
            title=f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            metadata={"created_by": "agent_api"}
        )
        db.add(session)
        await db.flush()
        session_id = session.id
    else:
        # Проверяем, что сессия существует и принадлежит пользователю
        session_result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == current_user.id
            )
        )
        session = session_result.scalar_one_or_none()
        if not session:
            raise HTTPException(
                status_code=404, detail="Chat session not found")

        # Обновляем device_id если передан
        if device_id and session.device_id != device_id:
            session.device_id = device_id

    # Проверяем устройство если указано
    if device_id:
        device_result = await db.execute(
            select(Device).where(
                Device.id == device_id,
                Device.user_id == current_user.id
            )
        )
        device = device_result.scalar_one_or_none()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

    # Сохраняем сообщение пользователя
    user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=payload.message,
        meta_data=payload.metadata
    )
    db.add(user_message)

    # Определяем, нужно ли создавать задачу
    agent = SimpleAgent()
    should_create_task = agent.should_create_task(payload.message)
    task_created = False
    task_id = None

    if should_create_task and device_id:
        try:
            # Создаем задачу
            task_data = agent.parse_task_from_message(
                payload.message, device_id)

            task_id = f"task_{uuid.uuid4().hex[:8]}"
            task = Task(
                id=task_id,
                user_id=current_user.id,
                device_id=device_id,
                title=task_data["title"],
                description=task_data["description"],
                payload={
                    "actions": task_data["actions"],
                    "metadata": task_data["metadata"]
                }
            )

            db.add(task)
            await db.flush()

            # Связываем сообщение с задачей
            user_message.task_id = task_id
            task_created = True

            # Публикуем событие для выполнения задачи
            try:
                await publish_event(f"deliver:task:{device_id}", {
                    "task_id": task_id,
                    "device_id": str(device_id),
                    "user_id": str(current_user.id)
                })
                logger.info(f"Published task {task_id} for device {device_id}")
            except Exception as e:
                logger.warning(f"Failed to publish task event: {e}")

        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            should_create_task = False

    # Генерируем ответ агента
    assistant_response = agent.generate_response(
        payload.message,
        task_created=task_created,
        task_id=task_id
    )

    # Сохраняем ответ агента
    assistant_message = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=assistant_response,
        metadata={
            "task_created": task_created,
            "task_id": task_id,
            "generated_by": "simple_agent"
        }
    )
    db.add(assistant_message)

    # Обновляем время сессии
    session.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(user_message)
    await db.refresh(assistant_message)

    return AgentChatResponse(
        session_id=session_id,
        message=ChatMessageResponse(
            id=user_message.id,
            session_id=user_message.session_id,
            role=user_message.role,
            content=user_message.content,
            created_at=user_message.created_at,
            metadata=user_message.meta_data,
            task_id=user_message.task_id,
        ),
        assistant_message=ChatMessageResponse(
            id=assistant_message.id,
            session_id=assistant_message.session_id,
            role=assistant_message.role,
            content=assistant_message.content,
            created_at=assistant_message.created_at,
            metadata=assistant_message.meta_data,
            task_id=None,
        ),
        task_created=task_created,
        task_id=task_id,
    )


@router.get("/capabilities")
async def get_agent_capabilities(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Получение информации о возможностях агента"""

    return {
        "capabilities": [
            {
                "name": "screenshot",
                "description": "Take screenshots of the desktop",
                "keywords": ["screenshot", "скриншот", "снимок экрана"],
                "example": "Сделай скриншот экрана"
            },
            {
                "name": "click",
                "description": "Click at specific coordinates or elements",
                "keywords": ["click", "кликни", "нажми", "клик"],
                "example": "Кликни на кнопку"
            },
            {
                "name": "type_text",
                "description": "Type text using keyboard",
                "keywords": ["type", "напечатай", "введи", "набери"],
                "example": "Напечатай 'Hello World'"
            },
            {
                "name": "window_management",
                "description": "Open, close, and manage application windows",
                "keywords": ["open", "close", "открой", "закрой"],
                "example": "Открой браузер"
            },
            {
                "name": "search",
                "description": "Find files, applications, or elements",
                "keywords": ["find", "найди", "поиск"],
                "example": "Найди файл document.pdf"
            }
        ],
        "supported_languages": ["ru", "en"],
        "version": "1.0.0",
        "agent_type": "simple_rule_based"
    }
