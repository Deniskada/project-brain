"""
API роуты для статистики
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging

from ...storage.chroma_client import ChromaClient

router = APIRouter()
logger = logging.getLogger(__name__)

# Глобальный клиент ChromaDB
chroma_client: ChromaClient = None

async def get_chroma_client() -> ChromaClient:
    """Получение ChromaDB клиента"""
    global chroma_client
    if chroma_client is None:
        chroma_client = ChromaClient()
        await chroma_client.initialize()
    return chroma_client

@router.get("/stats")
async def get_stats(chroma: ChromaClient = Depends(get_chroma_client)) -> Dict[str, Any]:
    """Получение общей статистики системы"""
    try:
        stats = await chroma.get_global_stats()
        
        return {
            "total_projects": stats.get("total_projects", 0),
            "total_chunks": stats.get("total_chunks", 0),
            "total_files": stats.get("total_files", 0),
            "storage_size": stats.get("storage_size", 0),
            "last_updated": stats.get("last_updated", None)
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {str(e)}")

@router.get("/stats/{project}")
async def get_project_stats(
    project: str,
    chroma: ChromaClient = Depends(get_chroma_client)
) -> Dict[str, Any]:
    """Получение статистики конкретного проекта"""
    try:
        stats = await chroma.get_project_stats(project)
        
        return {
            "project": project,
            "total_chunks": stats.get("total_chunks", 0),
            "total_files": stats.get("total_files", 0),
            "last_indexed": stats.get("last_indexed", None),
            "file_types": stats.get("file_types", {}),
            "top_files": stats.get("top_files", [])
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики проекта {project}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики проекта: {str(e)}")
