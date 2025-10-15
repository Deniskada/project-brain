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
            import os
            
            chroma_host = os.getenv("CHROMA_HOST", "chromadb").replace("http://", "").split(":")[0]
            chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
            
            logger.info(f"Подключение к ChromaDB: {chroma_host}:{chroma_port}")
            
            # ChromaDB 0.5.x - новый API
            self.chroma_client = chromadb.HttpClient(
                host=chroma_host,
                port=chroma_port
            )
            
            # Инициализация модели эмбеддингов
            logger.info("Загрузка модели эмбеддингов...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Получение или создание коллекции
            logger.info("Получение коллекции project_brain...")
            self.collection = self.chroma_client.get_or_create_collection(
                name="project_brain",
                metadata={"description": "Project Brain knowledge base"}
            )
            
            logger.info(f"✅ RAG Engine инициализирован успешно. Коллекция: {self.collection.name}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации RAG Engine: {e}", exc_info=True)
            raise
    
    def _detect_query_intent(self, query: str) -> Dict[str, Any]:
        """
        Определение намерения пользователя для точного поиска
        """
        query_lower = query.lower()
        intent = {
            'type': 'general',
            'preferred_doc_types': [],
            'keywords': []
        }
        
        # Вопросы "как сделать X" - пользователь хочет узнать процесс
        how_keywords = ['как', 'how', 'что нужно', 'каким образом', 'способ', 'метод', 
                        'процесс', 'инструкция', 'шаги']
        if any(kw in query_lower for kw in how_keywords):
            intent['type'] = 'how_to'
            intent['preferred_doc_types'] = ['route', 'handler', 'service']
            
            # Если спрашивают про создание/изменение - точно роуты
            action_keywords = ['создать', 'добавить', 'изменить', 'удалить', 'обновить',
                              'create', 'add', 'update', 'delete', 'modify']
            if any(kw in query_lower for kw in action_keywords):
                intent['preferred_doc_types'] = ['route', 'handler', 'api']
        
        # Вопросы про структуру данных - модели БД
        structure_keywords = ['поля', 'модель', 'таблица', 'schema', 'fields', 'структура',
                             'атрибуты', 'колонки', 'столбцы']
        if any(kw in query_lower for kw in structure_keywords):
            intent['type'] = 'structure'
            intent['preferred_doc_types'] = ['model', 'schema']
        
        # Вопросы про API
        api_keywords = ['api', 'endpoint', 'роут', 'route', 'запрос', 'request']
        if any(kw in query_lower for kw in api_keywords):
            intent['type'] = 'api'
            intent['preferred_doc_types'] = ['route', 'api']
        
        # Вопросы про бизнес-логику
        logic_keywords = ['логика', 'обработка', 'алгоритм', 'бизнес', 'правила']
        if any(kw in query_lower for kw in logic_keywords):
            intent['type'] = 'logic'
            intent['preferred_doc_types'] = ['service', 'handler']
        
        return intent
    
    def _rerank_results(
        self, 
        results: List[Dict[str, Any]], 
        intent: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Переранжирование результатов на основе намерения пользователя
        """
        preferred_types = intent.get('preferred_doc_types', [])
        
        if not preferred_types:
            return results
        
        # Присваиваем бонусы релевантности
        for result in results:
            doc_type = result.get('doc_type', 'other')
            
            # Сильный буст для точного соответствия типа
            if doc_type in preferred_types:
                boost_index = preferred_types.index(doc_type)
                # Первый в списке получает больший буст
                boost = 0.3 - (boost_index * 0.1)
                result['score'] = min(1.0, result['score'] + boost)
            
            # Небольшой штраф для несоответствующих типов
            elif len(preferred_types) > 0 and doc_type == 'model' and 'route' in preferred_types:
                result['score'] *= 0.7
        
        # Сортируем по новому score
        return sorted(results, key=lambda x: x['score'], reverse=True)
    
    async def retrieve_context(
        self, 
        query: str, 
        project: str = "staffprobot",
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Поиск релевантного контекста для запроса с умной приоритизацией
        """
        try:
            # Определение намерения пользователя
            intent = self._detect_query_intent(query)
            logger.info(f"Query intent: {intent['type']}, preferred types: {intent['preferred_doc_types']}")
            
            # Создание эмбеддинга запроса
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Двухэтапный поиск для "how_to" запросов
            context_docs = []
            
            if intent['type'] == 'how_to' and intent['preferred_doc_types']:
                # Этап 1: Ищем в предпочтительных типах документов
                try:
                    where_clause = {
                        "$and": [
                            {"project": project},
                            {"$or": [{"doc_type": dt} for dt in intent['preferred_doc_types']]}
                        ]
                    }
                    
                    results_priority = self.collection.query(
                        query_embeddings=[query_embedding],
                        n_results=top_k,
                        where=where_clause
                    )
                    
                    # Форматирование приоритетных результатов
                    if results_priority['documents'] and results_priority['documents'][0]:
                        for i, doc in enumerate(results_priority['documents'][0]):
                            context_docs.append({
                                "content": doc,
                                "file": results_priority['metadatas'][0][i].get('file', ''),
                                "lines": results_priority['metadatas'][0][i].get('lines', ''),
                                "type": results_priority['metadatas'][0][i].get('type', ''),
                                "doc_type": results_priority['metadatas'][0][i].get('doc_type', 'other'),
                                "score": 1 - results_priority['distances'][0][i] if results_priority['distances'] else 0.0
                            })
                    
                    logger.info(f"Found {len(context_docs)} results in priority types")
                
                except Exception as e:
                    logger.warning(f"Priority search failed: {e}, falling back to general search")
            
            # Если не нашли достаточно или это не how_to - общий поиск
            if len(context_docs) < top_k:
                remaining = top_k - len(context_docs)
                where_clause = {"project": project} if project else None
                
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k * 2,  # Берём больше для переранжирования
                    where=where_clause
                )
                
                # Форматирование результатов
                if results['documents'] and results['documents'][0]:
                    for i, doc in enumerate(results['documents'][0]):
                        doc_data = {
                            "content": doc,
                            "file": results['metadatas'][0][i].get('file', ''),
                            "lines": results['metadatas'][0][i].get('lines', ''),
                            "type": results['metadatas'][0][i].get('type', ''),
                            "doc_type": results['metadatas'][0][i].get('doc_type', 'other'),
                            "score": 1 - results['distances'][0][i] if results['distances'] else 0.0
                        }
                        
                        # Избегаем дублей
                        if not any(d['file'] == doc_data['file'] and d['lines'] == doc_data['lines'] 
                                  for d in context_docs):
                            context_docs.append(doc_data)
            
            # Переранжирование на основе намерения
            context_docs = self._rerank_results(context_docs, intent)
            
            # Возвращаем top_k лучших
            final_results = context_docs[:top_k]
            logger.info(f"Returning {len(final_results)} results after reranking")
            
            return final_results
            
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
        if not self.collection:
            logger.warning("ChromaDB недоступен, пропускаем сохранение документа")
            return
            
        try:
            # Создание эмбеддинга
            embedding = self.embedding_model.encode(content).tolist()
            
            # Уникальный ID: используем chunk_id или создаём хеш
            chunk_id = metadata.get('chunk_id', hash(f"{metadata.get('file', '')}_{metadata.get('start_line', 0)}_{content[:50]}"))
            doc_id = f"{project}_{chunk_id}"
            
            # Сохранение в ChromaDB (с обработкой дублей)
            try:
                self.collection.add(
                    embeddings=[embedding],
                    documents=[content],
                    metadatas=[metadata],
                    ids=[doc_id]
                )
            except Exception as e:
                # Если документ уже существует - пропускаем
                if "already exists" in str(e) or "duplicate" in str(e).lower():
                    pass  # Тихо пропускаем дубли
                else:
                    raise  # Другие ошибки пробрасываем
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении документа: {e}")
            # Не пробрасываем ошибку - просто логируем
    
    async def query(
        self,
        query: str,
        project: str = "staffprobot",
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Полный RAG запрос: поиск контекста + генерация ответа
        """
        try:
            # Поиск релевантного контекста
            context_docs = await self.retrieve_context(
                query=query,
                project=project,
                top_k=top_k
            )
            
            # Импорт Ollama клиента
            from ..llm.ollama_client import OllamaClient
            ollama = OllamaClient()
            await ollama.initialize()
            
            # Генерация ответа с контекстом
            answer = await ollama.generate_response(
                query=query,
                context=context_docs,
                max_tokens=1000
            )
            
            # Форматирование источников
            sources = []
            for doc in context_docs:
                sources.append({
                    "file": doc.get("file", ""),
                    "lines": doc.get("lines", ""),
                    "content": doc.get("content", "")[:200] + "...",
                    "score": doc.get("score", 0.0)
                })
            
            # Получение релевантных правил
            relevant_rules = await self.get_relevant_rules(
                file_path="",
                role=""
            )
            
            return {
                "answer": answer,
                "sources": sources,
                "relevant_rules": relevant_rules
            }
            
        except Exception as e:
            logger.error(f"Ошибка RAG запроса: {e}", exc_info=True)
            return {
                "answer": f"Ошибка при обработке запроса: {str(e)}",
                "sources": [],
                "relevant_rules": []
            }
