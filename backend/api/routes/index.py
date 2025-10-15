"""
API роуты для индексации проектов
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

from ...indexers.python_indexer import PythonIndexer
from ...indexers.markdown_indexer import MarkdownIndexer
from ...storage.chroma_client import ChromaClient

router = APIRouter()
logger = logging.getLogger(__name__)

class IndexRequest(BaseModel):
    project: str
    force_reindex: bool = False

class IndexResponse(BaseModel):
    status: str
    message: str
    indexed_files: int
    processing_time: float

# Глобальный клиент ChromaDB
chroma_client: ChromaClient = None

async def get_chroma_client() -> ChromaClient:
    """Получение ChromaDB клиента"""
    global chroma_client
    if chroma_client is None:
        chroma_client = ChromaClient()
        await chroma_client.initialize()
    return chroma_client

async def index_project_task(project: str, force_reindex: bool = False):
    """Фоновая задача индексации проекта"""
    try:
        import time
        start_time = time.time()
        
        # Инициализация клиентов
        chroma = await get_chroma_client()
        python_indexer = PythonIndexer()
        markdown_indexer = MarkdownIndexer()
        
        # Получение конфигурации проекта
        project_config = await chroma.get_project_config(project)
        if not project_config:
            logger.error(f"Проект {project} не найден в конфигурации")
            return
        
        indexed_files = 0
        
        # Индексация Python файлов
        python_files = await python_indexer.find_files(
            project_config["path"],
            project_config["index_patterns"],
            project_config["exclude_patterns"]
        )
        
        for file_path in python_files:
            if file_path.endswith('.py'):
                try:
                    chunks = await python_indexer.index_file(file_path)
                    await chroma.store_chunks(project, chunks)
                    indexed_files += 1
                    logger.info(f"Проиндексирован файл: {file_path}")
                except Exception as e:
                    logger.error(f"Ошибка индексации {file_path}: {e}")
        
        # Индексация Markdown файлов
        md_files = await markdown_indexer.find_files(
            project_config["path"],
            project_config["index_patterns"],
            project_config["exclude_patterns"]
        )
        
        for file_path in md_files:
            if file_path.endswith('.md'):
                try:
                    chunks = await markdown_indexer.index_file(file_path)
                    await chroma.store_chunks(project, chunks)
                    indexed_files += 1
                    logger.info(f"Проиндексирован файл: {file_path}")
                except Exception as e:
                    logger.error(f"Ошибка индексации {file_path}: {e}")
        
        processing_time = time.time() - start_time
        logger.info(f"Индексация завершена: {indexed_files} файлов за {processing_time:.2f}с")
        
    except Exception as e:
        logger.error(f"Ошибка при индексации проекта {project}: {e}")

@router.post("/index", response_model=IndexResponse)
async def index_project(
    request: IndexRequest,
    background_tasks: BackgroundTasks
):
    """
    Запуск индексации проекта
    """
    try:
        # Запуск фоновой задачи
        background_tasks.add_task(index_project_task, request.project, request.force_reindex)
        
        return IndexResponse(
            status="started",
            message=f"Индексация проекта {request.project} запущена в фоне",
            indexed_files=0,
            processing_time=0.0
        )
        
    except Exception as e:
        logger.error(f"Ошибка при запуске индексации: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка запуска индексации: {str(e)}")

@router.get("/index/status/{project}")
async def get_index_status(project: str):
    """Получение статуса индексации проекта"""
    try:
        chroma = await get_chroma_client()
        stats = await chroma.get_project_stats(project)
        
        return {
            "project": project,
            "status": "completed" if stats["total_chunks"] > 0 else "not_indexed",
            "total_chunks": stats["total_chunks"],
            "last_indexed": stats.get("last_indexed", None)
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении статуса: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения статуса: {str(e)}")
