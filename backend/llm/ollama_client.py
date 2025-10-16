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
        self.model = "qwen2.5:14b-instruct"  # Qwen 2.5 14B - баланс скорости и качества (8.9GB)
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
        max_tokens: int = 1000,
        project_name: str = "staffprobot"
    ) -> str:
        """
        Генерация ответа на основе запроса и контекста
        """
        try:
            logger.info(f"Генерация ответа с моделью: {self.model} для проекта: {project_name}")
            
            # Формирование промпта
            prompt = self._build_prompt(query, context, project_name)
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
                        "temperature": 0.3,  # Меньше креативности = точнее ответы
                        "top_p": 0.85,
                        "repeat_penalty": 1.2,  # Избегаем повторений
                        "num_ctx": 4096  # Больше контекста
                    }
                },
                timeout=90  # 90 секунд достаточно для 14B
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
    
    def _build_prompt(self, query: str, context: List[Dict[str, Any]], project_name: str = "staffprobot") -> str:
        """Построение промпта для LLM с учётом типов документов"""
        
        # Определяем типы документов в контексте
        doc_types = {}
        for doc in context:
            doc_type = doc.get('doc_type', 'other')
            doc_types.setdefault(doc_type, []).append(doc)
        
        # Описания проектов
        project_descriptions = {
            "staffprobot": "StaffProBot - система управления персоналом, контроль смен, учёт рабочего времени",
            "project-brain": "Project Brain - система управления знаниями с RAG, индексация кода, AI-ассистент"
        }
        
        project_desc = project_descriptions.get(project_name, project_name)
        
        # Системный промпт с динамическим именем проекта
        other_projects = {
            "staffprobot": ["project-brain", "Project Brain"],
            "project-brain": ["staffprobot", "StaffProBot"]
        }
        excluded = other_projects.get(project_name, [])
        
        system_prompt = f"""Ты - эксперт по проекту "{project_desc}". 
Твоя задача - отвечать на вопросы о коде, архитектуре и функциональности ИМЕННО ЭТОГО проекта: {project_name}.

КРИТИЧЕСКИ ВАЖНО:
- Контекст ниже относится ТОЛЬКО к проекту {project_name}
- НИКОГДА не упоминай проекты: {', '.join(excluded)}
- НИКОГДА не выдумывай несуществующие файлы или код
- Если файл не упомянут в контексте - значит его НЕТ в проекте

Правила:
1. Отвечай на русском языке, кратко и конкретно
2. ОБЯЗАТЕЛЬНО указывай РЕАЛЬНЫЕ файлы и строки из контекста ниже
3. Если в контексте есть роуты (routes) или хендлеры (handlers) - используй их ПЕРВЫМИ
4. Для вопросов "как сделать" - показывай ТОЛЬКО код из контекста
5. Если информации нет в контексте - скажи "В текущей кодовой базе такой информации нет"
6. НЕ придумывай пути к файлам - используй ТОЛЬКО из контекста

Контекст из кодовой базы проекта {project_name} (упорядочен по важности):"""

        # Добавление контекста с приоритизацией
        context_text = ""
        context_order = ['documentation', 'route', 'handler', 'api', 'service', 'form', 'model', 'schema', 'other']
        
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
