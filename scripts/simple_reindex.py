#!/usr/bin/env python3
"""
Простой скрипт переиндексации - запускается внутри контейнера
"""
import asyncio
import sys
sys.path.insert(0, '/app')

from backend.indexers.simple_project_indexer import SimpleProjectIndexer
from backend.indexers.python_indexer import PythonIndexer
from backend.indexers.markdown_indexer import MarkdownIndexer
from backend.rag.engine import RAGEngine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reindex_project(project_name: str):
    """Переиндексация проекта"""
    logger.info(f"🚀 Начало переиндексации: {project_name}")
    
    # Инициализация
    project_indexer = SimpleProjectIndexer()
    project_indexer.load_config()
    python_indexer = PythonIndexer()
    markdown_indexer = MarkdownIndexer()
    rag_engine = RAGEngine()
    await rag_engine.initialize()
    
    stats = {
        'total_files': 0,
        'total_chunks': 0,
        'errors': 0
    }
    
    # Индексация
    async for file_info in project_indexer.iter_project_files(project_name):
        try:
            file_path = file_info['file_path']
            file_type = file_info['file_type']
            relative_path = file_info['relative_path']
            
            stats['total_files'] += 1
            
            # Индексация файла
            chunks = []
            if file_type == 'python':
                chunks = await python_indexer.index_file(file_path)
            elif file_type == 'markdown':
                chunks = await markdown_indexer.index_file(file_path)
            
            # Загрузка чанков
            for chunk in chunks:
                doc_type = python_indexer._classify_doc_type(relative_path) if file_type == 'python' else 'documentation'
                
                await rag_engine.store_document(
                    project=project_name,
                    content=chunk['content'],
                    metadata={
                        'file': relative_path,
                        'type': chunk['type'],
                        'doc_type': doc_type,
                        'start_line': chunk.get('start_line', 0),
                        'end_line': chunk.get('end_line', 0),
                        'lines': chunk.get('lines', '0-0'),
                        'project': project_name,
                        'chunk_id': chunk.get('chunk_id', hash(chunk['content'][:100]))
                    }
                )
                stats['total_chunks'] += 1
            
            # Логируем прогресс
            if stats['total_files'] % 10 == 0:
                logger.info(f"📊 Обработано файлов: {stats['total_files']}, чанков: {stats['total_chunks']}")
        
        except Exception as e:
            stats['errors'] += 1
            logger.error(f"❌ Ошибка обработки {relative_path}: {e}")
    
    logger.info(f"✅ Индексация завершена: {stats}")
    return stats

if __name__ == "__main__":
    project = sys.argv[1] if len(sys.argv) > 1 else "staffprobot"
    asyncio.run(reindex_project(project))

