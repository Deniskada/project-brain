#!/usr/bin/env python3
"""
БЫСТРАЯ полная переиндексация StaffProBot
БЕЗ QA пар - просто нормальная индексация кода
"""
import sys
import logging
sys.path.insert(0, '/app')

from backend.indexers.simple_project_indexer import SimpleProjectIndexer
from backend.indexers.python_indexer import PythonIndexer
from backend.indexers.markdown_indexer import MarkdownIndexer
from backend.rag.engine import RAGEngine
import asyncio

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def fast_reindex():
    """Быстрая переиндексация"""
    logger.info("🚀 БЫСТРАЯ ПЕРЕИНДЕКСАЦИЯ STAFFPROBOT")
    
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
    async for file_info in project_indexer.iter_project_files('staffprobot'):
        try:
            file_path = file_info['file_path']
            file_type = file_info['file_type']
            relative_path = file_info['relative_path']
            
            stats['total_files'] += 1
            
            # Выбираем индексатор
            if file_type == 'python':
                chunks = await python_indexer.index_file(file_path)
            elif file_type == 'markdown':
                chunks = await markdown_indexer.index_file(file_path)
            else:
                continue
            
            # Сохраняем чанки
            for chunk in chunks:
                await rag_engine.store_document(
                    project='staffprobot',
                    content=chunk['content'],
                    metadata=chunk
                )
                stats['total_chunks'] += 1
            
            if stats['total_files'] % 50 == 0:
                logger.info(f"  📄 Обработано файлов: {stats['total_files']}, чанков: {stats['total_chunks']}")
        
        except Exception as e:
            stats['errors'] += 1
            logger.error(f"❌ Ошибка обработки {file_info.get('file_path', '?')}: {e}")
    
    logger.info(f"\n✅ ПЕРЕИНДЕКСАЦИЯ ЗАВЕРШЕНА!")
    logger.info(f"  • Файлов: {stats['total_files']}")
    logger.info(f"  • Чанков: {stats['total_chunks']}")
    logger.info(f"  • Ошибок: {stats['errors']}")

if __name__ == "__main__":
    asyncio.run(fast_reindex())

