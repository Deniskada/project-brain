"""
RAG Engine - основной движок для поиска и генерации ответов
"""
import logging
from typing import List, Dict, Any, Optional
import asyncio
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

class RAGEngine:
    def __init__(self):
        self.chroma_client = None
        self.embedding_model = None
        self.collection = None
        
    async def initialize(self):
        """Инициализация RAG engine"""
        try:
            # Инициализация ChromaDB
            self.chroma_client = chromadb.HttpClient(
                host="chromadb",
                port=8000
            )
            
            # Инициализация модели эмбеддингов
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Получение или создание коллекции
            try:
                self.collection = self.chroma_client.get_collection("project_brain")
            except:
                self.collection = self.chroma_client.create_collection(
                    name="project_brain",
                    metadata={"description": "Project Brain knowledge base"}
                )
            
            logger.info("RAG Engine инициализирован успешно")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации RAG Engine: {e}")
            raise
    
    async def retrieve_context(
        self, 
        query: str, 
        project: str = "staffprobot",
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Поиск релевантного контекста для запроса
        """
        try:
            # Создание эмбеддинга запроса
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Поиск в ChromaDB
            where_clause = {"project": project} if project else None
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause
            )
            
            # Форматирование результатов
            context_docs = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    context_docs.append({
                        "content": doc,
                        "file": results['metadatas'][0][i].get('file', ''),
                        "lines": results['metadatas'][0][i].get('lines', ''),
                        "type": results['metadatas'][0][i].get('type', ''),
                        "score": 1 - results['distances'][0][i] if results['distances'] else 0.0
                    })
            
            return context_docs
            
        except Exception as e:
            logger.error(f"Ошибка при поиске контекста: {e}")
            return []
    
    async def get_relevant_rules(
        self,
        file_path: str = "",
        role: str = "",
        module: str = ""
    ) -> List[str]:
        """
        Получение релевантных правил для контекста
        """
        try:
            # Построение запроса для поиска правил
            query_parts = []
            
            if role:
                query_parts.append(f"роль {role}")
            if file_path:
                if "routes" in file_path:
                    query_parts.append("роуты")
                if "owner" in file_path:
                    query_parts.append("владелец")
                if "manager" in file_path:
                    query_parts.append("управляющий")
                if "employee" in file_path:
                    query_parts.append("сотрудник")
            if module:
                query_parts.append(module)
            
            if not query_parts:
                return []
            
            query = " ".join(query_parts)
            
            # Поиск правил в базе знаний
            results = self.collection.query(
                query_texts=[query],
                n_results=10,
                where={"type": "rule"}
            )
            
            # Извлечение правил
            rules = []
            if results['documents'] and results['documents'][0]:
                for doc in results['documents'][0]:
                    rules.append(doc)
            
            return rules[:5]  # Ограничиваем количество правил
            
        except Exception as e:
            logger.error(f"Ошибка при получении правил: {e}")
            return []
    
    async def store_document(
        self,
        project: str,
        content: str,
        metadata: Dict[str, Any]
    ):
        """Сохранение документа в векторную БД"""
        try:
            # Создание эмбеддинга
            embedding = self.embedding_model.encode(content).tolist()
            
            # Сохранение в ChromaDB
            self.collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata],
                ids=[f"{project}_{metadata.get('file', '')}_{metadata.get('chunk_id', 0)}"]
            )
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении документа: {e}")
            raise
