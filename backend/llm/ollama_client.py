"""
Ollama клиент для работы с локальной LLM
"""
import logging
import httpx
from typing import List, Dict, Any, Optional
import json
import os

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, base_url: str = None):
        # Читаем URL из переменной окружения или используем значение по умолчанию
        self.base_url = base_url or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = "qwen2.5:14b-instruct"  # Qwen 2.5 14B - лучшая для русского! (8.9GB)
        self.fallback_model = "codellama:13b-instruct"  # Fallback модель (7.4GB)
        logger.info(f"OllamaClient инициализирован с base_url: {self.base_url}")
        
    async def initialize(self):
        """Инициализация клиента (пропускаем проверку)"""
        logger.info(f"Ollama клиент инициализирован с URL: {self.base_url}")
        logger.info(f"Модель: {self.model}, Fallback: {self.fallback_model}")
    
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
            logger.info(f"Генерация ответа с моделью: {self.model}")
            
            # Формирование промпта
            prompt = self._build_prompt(query, context)
            logger.info(f"Промпт: {prompt[:100]}...")
            
            # Запрос к Ollama через requests
            import requests
            response = requests.post(
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
                },
                timeout=60
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
        """Построение промпта для LLM с учётом типов документов"""
        
        # Определяем типы документов в контексте
        doc_types = {}
        for doc in context:
            doc_type = doc.get('doc_type', 'other')
            doc_types.setdefault(doc_type, []).append(doc)
        
        # Системный промпт
        system_prompt = """Ты - эксперт по проекту StaffProBot, система управления персоналом. 
Твоя задача - отвечать на вопросы о коде, архитектуре и функциональности проекта.

Правила:
1. Отвечай на русском языке, кратко и конкретно
2. ОБЯЗАТЕЛЬНО указывай файлы и строки кода из контекста
3. Если в контексте есть роуты (routes) или хендлеры (handlers) - используй их ПЕРВЫМИ для ответа
4. Для вопросов "как сделать" - показывай конкретный код и шаги
5. Если не знаешь точного ответа - скажи честно

Контекст из кодовой базы (упорядочен по важности):"""

        # Добавление контекста с приоритизацией
        context_text = ""
        context_order = ['route', 'handler', 'api', 'service', 'form', 'model', 'schema', 'other']
        
        context_num = 1
        for doc_type in context_order:
            if doc_type in doc_types:
                for doc in doc_types[doc_type]:
                    # Метка типа документа для лучшего понимания
                    type_label = {
                        'route': '🔗 РОУТ (API endpoint)',
                        'handler': '⚡ ХЕНДЛЕР (обработчик)',
                        'api': '📡 API',
                        'service': '🔧 СЕРВИС (бизнес-логика)',
                        'form': '📝 ФОРМА',
                        'model': '🗄️ МОДЕЛЬ БД',
                        'schema': '📋 СХЕМА',
                        'other': '📄 ДОКУМЕНТАЦИЯ'
                    }.get(doc_type, '📄')
                    
                    file_info = f"{type_label}\nФайл: {doc.get('file', 'неизвестно')}"
                    if doc.get('lines'):
                        file_info += f"\nСтроки: {doc['lines']}"
                    
                    # Обрезаем слишком длинный контент
                    content = doc.get('content', '')
                    if len(content) > 800:
                        content = content[:800] + "\n... (контент обрезан)"
                    
                    context_text += f"\n\n--- Контекст {context_num} ---\n{file_info}\n\n{content}"
                    context_num += 1
        
        # Формирование полного промпта
        full_prompt = f"""{system_prompt}

{context_text}

Вопрос пользователя: {query}

Твой ответ (начни сразу с конкретной информации):"""

        return full_prompt
    
    async def test_connection(self) -> bool:
        """Тестирование подключения к Ollama"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except:
            return False
