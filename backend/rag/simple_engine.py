"""
Простой RAG Engine без ChromaDB для тестирования
"""
import logging
from typing import List, Dict, Any, Optional
import asyncio
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class SimpleRAGEngine:
    def __init__(self):
        self.embedding_model = None
        self.ollama_client = None
        
    async def initialize(self):
        """Инициализация простого RAG engine"""
        try:
            # Инициализация модели эмбеддингов
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Простая инициализация Ollama клиента
            from ..llm.ollama_client import OllamaClient
            self.ollama_client = OllamaClient()
            await self.ollama_client.initialize()
            
            logger.info("Simple RAG Engine инициализирован успешно")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации Simple RAG Engine: {e}")
            raise
    
    async def query(self, query: str, project: str = "staffprobot") -> Dict[str, Any]:
        """
        Простой запрос без ChromaDB - только генерация через Ollama
        """
        try:
            # Простой ответ без поиска в базе знаний
            response = await self.ollama_client.generate_response(
                query=f"Пользователь спрашивает: {query}\n\n"
                      f"Контекст: работа с проектом {project}\n\n"
                      f"Ответь кратко и по делу:",
                context=[],
                max_tokens=500
            )
            
            return {
                "answer": response,
                "sources": [],
                "relevant_rules": []
            }
            
        except Exception as e:
            logger.error(f"Ошибка при обработке запроса: {e}")
            return {
                "answer": f"Произошла ошибка при обработке запроса: {e}",
                "sources": [],
                "relevant_rules": []
            }
    
    async def get_relevant_rules(self, file_path: str = "", role: str = "") -> List[str]:
        """
        Возвращает базовые правила для тестирования
        """
        basic_rules = [
            "Используй type hints для всех функций",
            "Следуй принципам SOLID",
            "Логируй важные события",
            "Обрабатывай ошибки корректно"
        ]
        
        if "routes" in file_path:
            basic_rules.append("Используй правильные префиксы для роутов")
        
        if role:
            basic_rules.append(f"Учитывай роль: {role}")
        
        return basic_rules[:3]  # Ограничиваем количество
