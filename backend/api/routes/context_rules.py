"""
API роуты для контекстных правил Cursor
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
import logging

from ...rag.engine import RAGEngine

router = APIRouter()
logger = logging.getLogger(__name__)

# Глобальный RAG engine
rag_engine: RAGEngine = None

async def get_rag_engine() -> RAGEngine:
    """Получение RAG engine"""
    global rag_engine
    if rag_engine is None:
        rag_engine = RAGEngine()
        await rag_engine.initialize()
    return rag_engine

@router.get("/context-rules")
async def get_context_rules(
    file: Optional[str] = Query(None, description="Путь к файлу"),
    role: Optional[str] = Query(None, description="Роль пользователя"),
    module: Optional[str] = Query(None, description="Модуль системы"),
    rag: RAGEngine = Depends(get_rag_engine)
) -> Dict[str, Any]:
    """
    Получение контекстных правил для Cursor
    Возвращает только релевантные правила (1-2K токенов вместо 10K)
    """
    try:
        # Определение контекста на основе параметров
        context = {
            "file": file,
            "role": role,
            "module": module
        }
        
        # Получение релевантных правил
        relevant_rules = await rag.get_relevant_rules(
            file_path=file or "",
            role=role or "",
            module=module or ""
        )
        
        # Подсчет токенов (примерно 4 символа = 1 токен)
        total_chars = sum(len(rule) for rule in relevant_rules)
        estimated_tokens = total_chars // 4
        
        return {
            "rules": relevant_rules,
            "context": context,
            "estimated_tokens": estimated_tokens,
            "rules_count": len(relevant_rules)
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении контекстных правил: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения правил: {str(e)}")

@router.get("/context-rules/categories")
async def get_rule_categories() -> Dict[str, List[str]]:
    """Получение доступных категорий правил"""
    return {
        "roles": ["owner", "manager", "employee", "admin", "moderator"],
        "file_types": ["python", "markdown", "html", "javascript", "css"],
        "modules": [
            "web_routes", "bot_handlers", "database", "templates", 
            "services", "domain_entities", "api", "scheduler"
        ],
        "contexts": [
            "authentication", "database_queries", "template_rendering",
            "api_endpoints", "bot_commands", "file_operations"
        ]
    }
