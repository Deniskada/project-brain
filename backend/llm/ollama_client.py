"""
Ollama клиент для работы с локальной LLM
"""
import logging
import httpx
from typing import List, Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, base_url: str = "http://ollama:11434"):
        self.base_url = base_url
        self.model = "codellama:34b-instruct"  # Основная модель
        self.fallback_model = "codellama:13b-instruct"  # Fallback модель
        
    async def initialize(self):
        """Инициализация клиента"""
        try:
            # Проверка доступности Ollama
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    available_models = [m["name"] for m in models]
                    
                    if self.model not in available_models:
                        logger.warning(f"Модель {self.model} не найдена. Доступные: {available_models}")
                        if self.fallback_model in available_models:
                            self.model = self.fallback_model
                            logger.info(f"Используется fallback модель: {self.model}")
                        else:
                            raise Exception("Ни одна из моделей не доступна")
                    
                    logger.info(f"Ollama клиент инициализирован с моделью: {self.model}")
                else:
                    raise Exception(f"Ollama недоступен: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Ошибка инициализации Ollama клиента: {e}")
            raise
    
    async def generate_response(
        self,
        query: str,
        context: List[Dict[str, Any]],
        max_tokens: int = 1000
    ) -> str:
        """
        Генерация ответа на основе запроса и контекста
        """
        try:
            # Формирование промпта
            prompt = self._build_prompt(query, context)
            
            # Запрос к Ollama
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "num_predict": max_tokens,
                            "temperature": 0.7,
                            "top_p": 0.9
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "Ошибка генерации ответа")
                else:
                    logger.error(f"Ошибка запроса к Ollama: {response.status_code}")
                    return "Ошибка при генерации ответа"
                    
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа: {e}")
            return f"Ошибка при генерации ответа: {str(e)}"
    
    def _build_prompt(self, query: str, context: List[Dict[str, Any]]) -> str:
        """Построение промпта для LLM"""
        
        # Системный промпт
        system_prompt = """Ты - эксперт по проекту StaffProBot, система управления персоналом. 
Твоя задача - отвечать на вопросы о коде, архитектуре и функциональности проекта.

Правила:
1. Отвечай на русском языке
2. Будь точным и конкретным
3. Ссылайся на конкретные файлы и строки кода
4. Если не знаешь ответа, честно скажи об этом
5. Предлагай практические решения

Контекст из кодовой базы:"""

        # Добавление контекста
        context_text = ""
        for i, doc in enumerate(context, 1):
            file_info = f"Файл: {doc.get('file', 'неизвестно')}"
            if doc.get('lines'):
                file_info += f", строки: {doc['lines']}"
            
            context_text += f"\n\n--- Контекст {i} ---\n{file_info}\n{doc.get('content', '')}"
        
        # Формирование полного промпта
        full_prompt = f"""{system_prompt}

{context_text}

Вопрос: {query}

Ответ:"""

        return full_prompt
    
    async def test_connection(self) -> bool:
        """Тестирование подключения к Ollama"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except:
            return False
