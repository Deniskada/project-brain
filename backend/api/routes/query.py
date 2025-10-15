"""
API роуты для запросов к AI
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import logging

from ...rag.engine import RAGEngine  # Полноценный RAG с ChromaDB
from ...rag.simple_engine import SimpleRAGEngine  # Fallback
from ...llm.ollama_client import OllamaClient

router = APIRouter()
logger = logging.getLogger(__name__)

class QueryRequest(BaseModel):
    query: str
    project: str = "staffprobot"
    context: Optional[Dict[str, Any]] = None
    max_tokens: Optional[int] = 1000

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    relevant_rules: Optional[List[str]] = None
    processing_time: float

# Глобальные клиенты (инициализируются при первом запросе)
rag_engine: Optional[RAGEngine] = None
ollama_client: Optional[OllamaClient] = None

async def get_rag_engine() -> RAGEngine:
    """Получение RAG engine с ChromaDB (ленивая инициализация)"""
    global rag_engine
    if rag_engine is None:
        try:
            rag_engine = RAGEngine()
            await rag_engine.initialize()
            logger.info("✅ RAG Engine с ChromaDB инициализирован")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации RAG Engine: {e}")
            # Fallback на SimpleRAGEngine
            rag_engine = SimpleRAGEngine()
            await rag_engine.initialize()
            logger.warning("⚠️ Используется SimpleRAGEngine (без ChromaDB)")
    return rag_engine

async def get_ollama_client() -> OllamaClient:
    """Получение Ollama клиента (ленивая инициализация)"""
    global ollama_client
    if ollama_client is None:
        ollama_client = OllamaClient()
        await ollama_client.initialize()
    return ollama_client

@router.post("/query", response_model=QueryResponse)
async def query_ai(
    request: QueryRequest,
    rag: SimpleRAGEngine = Depends(get_rag_engine),
    ollama: OllamaClient = Depends(get_ollama_client)
):
    """
    Основной endpoint для запросов к AI
    """
    import time
    start_time = time.time()
    
    try:
        # Получение релевантного контекста
        result = await rag.query(
            query=request.query,
            project=request.project
        )
        
        # Результат уже готов из RAG
        answer = result.get("answer", "Ошибка генерации ответа")
        relevant_rules = result.get("relevant_rules", [])
        sources = result.get("sources", [])
        
        processing_time = time.time() - start_time
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            relevant_rules=relevant_rules,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обработки запроса: {str(e)}")

@router.get("/query/test")
async def test_query():
    """Тестовый endpoint для проверки работы"""
    return {"message": "Query API работает!", "status": "ok"}
