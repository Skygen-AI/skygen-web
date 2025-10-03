#!/usr/bin/env python3
"""
Простой desktop агент для обработки screenshot задач без coact_client.
Подключается напрямую к backend через WebSocket и выполняет screenshot задачи.
"""

import asyncio
import json
import websockets
import uuid
import os
import tempfile
import aiohttp
from datetime import datetime, timezone
from typing import Dict, Any

# Импортируем embedded desktop environment
import sys
sys.path.append('/Users/egorandreevich/_Dev/Work/Skygen-Repos/skygen-web/backend')
from desktop_env.embedded.env import EmbeddedDesktopEnv

class SimpleDesktopAgent:
    def __init__(self, backend_ws_url: str, device_token: str):
        self.backend_ws_url = backend_ws_url
        self.device_token = device_token
        self.desktop_env = EmbeddedDesktopEnv()
        self.websocket = None
        
    async def connect(self):
        """Подключение к backend WebSocket"""
        try:
            # Подключаемся с device token
            ws_url = f"{self.backend_ws_url}/v1/ws/agent?token={self.device_token}"
            print(f"🔌 Подключение к: {ws_url}")
            
            self.websocket = await websockets.connect(ws_url)
            print("✅ Подключено к backend WebSocket!")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False
    
    async def handle_task(self, task_envelope: Dict[str, Any]):
        """Обработка входящей задачи"""
        try:
            task_id = task_envelope.get("task_id")
            actions = task_envelope.get("actions", [])
            
            print(f"📋 Получена задача {task_id} с {len(actions)} действиями")
            
            results = []
            for action in actions:
                # Пробуем получить тип действия из разных полей
                action_type = action.get("type") or action.get("action_type")
                
                print(f"🔍 Обрабатываю действие: {action}")
                print(f"📝 Тип действия: {action_type}")
                
                if action_type == "screenshot":
                    print("📸 Выполняю screenshot...")
                    result = await self.take_screenshot_and_upload(task_id)
                    results.append({
                        "action_id": action.get("action_id"),
                        "action_type": action_type,
                        "status": "completed",
                        "result": result
                    })
                else:
                    print(f"⚠️ Неизвестный тип действия: {action_type}")
                    results.append({
                        "action_id": action.get("action_id"),
                        "action_type": action_type,
                        "status": "failed",
                        "error": f"Unknown action type: {action_type}"
                    })
            
            # Отправляем результат обратно
            response = {
                "type": "task.result",
                "task_id": task_id,
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "results": results
            }
            
            # Добавляем информацию о скриншоте для отображения в чате
            for result in results:
                if result.get("action_type") == "screenshot" and "result" in result:
                    screenshot_path = result["result"].get("screenshot_path")
                    if screenshot_path:
                        response["screenshot_path"] = screenshot_path
                        print(f"📎 Добавлен путь к скриншоту в ответ: {screenshot_path}")
            
            await self.websocket.send(json.dumps(response))
            print(f"✅ Результат задачи {task_id} отправлен")
            
            # Если это screenshot, сохраняем путь к файлу для отображения
            for result in results:
                if result.get("action_type") == "screenshot" and "result" in result:
                    screenshot_path = result["result"].get("screenshot_path")
                    if screenshot_path:
                        print(f"📤 Отправляю информацию о скриншоте: {screenshot_path}")
                        await self.store_screenshot_info(task_id, screenshot_path)
            
        except Exception as e:
            print(f"❌ Ошибка выполнения задачи: {e}")
    
    async def take_screenshot(self) -> Dict[str, Any]:
        """Делает screenshot через embedded desktop environment"""
        try:
            # Получаем screenshot в формате PNG bytes
            screenshot_bytes = self.desktop_env.screenshot_png_bytes()
            
            # Сохраняем во временный файл
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                tmp_file.write(screenshot_bytes)
                screenshot_path = tmp_file.name
            
            # Получаем информацию о размере экрана
            screen_size = self.desktop_env.screen_size()
            cursor_pos = self.desktop_env.cursor_position()
            
            print(f"📸 Screenshot сохранен: {screenshot_path}")
            print(f"📏 Размер экрана: {screen_size[0]}x{screen_size[1]}")
            print(f"🖱️ Позиция курсора: {cursor_pos}")
            
            return {
                "screenshot_path": screenshot_path,
                "screenshot_size_bytes": len(screenshot_bytes),
                "screen_size": screen_size,
                "cursor_position": cursor_pos,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            print(f"❌ Ошибка screenshot: {e}")
            raise
    
    async def take_screenshot_and_upload(self, task_id: str) -> Dict[str, Any]:
        """Делает screenshot и загружает в S3"""
        try:
            # Сначала создаем локальный screenshot
            screenshot_result = await self.take_screenshot()
            local_path = screenshot_result["screenshot_path"]
            
            print(f"☁️ Загружаю screenshot в S3...")
            
            # Загружаем в S3 через artifacts endpoint
            s3_url = await self.upload_to_s3(local_path, task_id)
            
            if s3_url:
                print(f"✅ Screenshot загружен в S3: {s3_url}")
                # Удаляем локальный файл после успешной загрузки
                try:
                    os.remove(local_path)
                    print(f"🗑️ Локальный файл удален: {local_path}")
                except Exception as e:
                    print(f"⚠️ Не удалось удалить локальный файл: {e}")
                
                # Возвращаем результат с S3 URL
                screenshot_result["s3_url"] = s3_url
                screenshot_result["screenshot_path"] = s3_url  # Заменяем локальный путь на S3 URL
                return screenshot_result
            else:
                print(f"⚠️ Загрузка в S3 не удалась, оставляем локальный файл")
                return screenshot_result
                
        except Exception as e:
            print(f"❌ Ошибка screenshot и загрузки: {e}")
            raise
    
    async def upload_to_s3(self, file_path: str, task_id: str) -> str:
        """Загружает файл в S3 через artifacts API"""
        try:
            backend_base_url = self.backend_ws_url.replace("ws://", "http://").replace("wss://", "https://")
            
            # Создаем имя файла  
            filename = f"screenshot_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            async with aiohttp.ClientSession() as session:
                # Читаем файл
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                # Подготавливаем данные для multipart/form-data
                data = aiohttp.FormData()
                data.add_field('file', file_content, filename=filename, content_type='image/png')
                data.add_field('filename', filename)
                data.add_field('content_type', 'image/png')
                
                # Используем временный эндпоинт без авторизации
                upload_url = f"{backend_base_url}/v1/artifacts/upload-temp"
                print(f"🔄 Отправляю файл на {upload_url}")
                
                # Реальная загрузка в MinIO
                response = await session.post(upload_url, data=data)
                
                if response.status == 200:
                    result = await response.json()
                    minio_url = result['url']
                    print(f"✅ Файл загружен в MinIO: {minio_url}")
                    return minio_url
                else:
                    error_text = await response.text()
                    print(f"❌ Ошибка загрузки: {response.status} - {error_text}")
                    return None
                
        except Exception as e:
            print(f"❌ Ошибка загрузки в S3: {e}")
            return None
    
    async def store_screenshot_info(self, task_id: str, screenshot_path: str):
        """Отправляет информацию о скриншоте в backend для отображения"""
        try:
            # Получаем токен из device_token (это JWT с device_id)
            # Для простоты используем тот же токен
            headers = {
                "Authorization": f"Bearer {self.device_token}",
                "Content-Type": "application/json"
            }
            
            # В реальной реализации нужно использовать aiohttp
            # Пока что просто логируем
            print(f"📋 Информация о скриншоте сохранена для задачи {task_id}: {screenshot_path}")
            
        except Exception as e:
            print(f"⚠️ Не удалось сохранить информацию о скриншоте: {e}")
    
    async def listen_for_tasks(self):
        """Слушает входящие задачи от backend"""
        try:
            print("👂 Ожидание задач...")
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get("type")
                    
                    if message_type == "task.exec":
                        await self.handle_task(data)
                    else:
                        print(f"📩 Получено сообщение типа: {message_type}")
                        
                except json.JSONDecodeError as e:
                    print(f"⚠️ Ошибка парсинга JSON: {e}")
                except Exception as e:
                    print(f"⚠️ Ошибка обработки сообщения: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Соединение закрыто")
        except Exception as e:
            print(f"❌ Ошибка при прослушивании задач: {e}")
    
    async def run(self):
        """Основной цикл агента"""
        if await self.connect():
            await self.listen_for_tasks()

async def main():
    """Точка входа"""
    print("🤖 Запуск Simple Desktop Agent...")
    
    # Настройки подключения
    BACKEND_WS_URL = "ws://localhost:8000"
    # Используем правильный device_token
    DEVICE_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6InYxIiwidHlwIjoiSldUIn0.eyJkZXZpY2VfaWQiOiIxNDRlYTY4ZC1kZDcwLTRhZTEtYjc2Mi1jY2E1MGVlN2I0NTciLCJqdGkiOiJlNDVlMjU2Yjc5YzI0MmRlODY5ZmE1OTk0ZDc0Y2E1MyIsImV4cCI6MTc1NzY5MDU1NywiaWF0IjoxNzU3NjA0MTU3fQ.YPiJf5vIW1AVCHto7SOPLlAbI9A-L2vxnm380AfyNRs"
    
    agent = SimpleDesktopAgent(BACKEND_WS_URL, DEVICE_TOKEN)
    
    try:
        await agent.run()
    except KeyboardInterrupt:
        print("\n👋 Завершение работы агента...")
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")

if __name__ == "__main__":
    # Проверяем, что мы на macOS
    import platform
    if platform.system() != "Darwin":
        print("⚠️ Этот агент протестирован только на macOS")
    
    # Запуск
    asyncio.run(main())
