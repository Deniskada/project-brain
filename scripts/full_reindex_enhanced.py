#!/usr/bin/env python3
"""
Полная переиндексация с улучшениями:
1. Генерация QA пар из кода
2. Индексация с расширенными метаданными
3. Создание специализированных коллекций
4. Оценка качества
"""
import asyncio
import sys
import logging
from pathlib import Path

sys.path.insert(0, '/app')

from backend.indexers.simple_project_indexer import SimpleProjectIndexer
from backend.indexers.python_indexer import PythonIndexer
from backend.indexers.markdown_indexer import MarkdownIndexer
from backend.rag.engine import RAGEngine
import subprocess

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def full_reindex(project_name: str = "staffprobot"):
    """Полная переиндексация с улучшениями"""
    
    logger.info("=" * 80)
    logger.info("🚀 ПОЛНАЯ ПЕРЕИНДЕКСАЦИЯ С УЛУЧШЕНИЯМИ")
    logger.info(f"📦 Проект: {project_name}")
    logger.info("=" * 80)
    logger.info("")
    
    # ШАГ 1: Генерация обучающих QA пар
    logger.info("📝 ШАГ 1: Генерация обучающих QA пар из кода")
    logger.info("-" * 80)
    try:
        result = subprocess.run(
            ['python', '/app/scripts/auto_generate_qa_pairs.py', f'/projects/{project_name}'],
            capture_output=True,
            text=True,
            timeout=60
        )
        logger.info(result.stdout)
        if result.returncode != 0:
            logger.warning(f"⚠️ Генерация QA пар завершилась с ошибкой: {result.stderr}")
        else:
            logger.info("✅ QA пары сгенерированы")
    except Exception as e:
        logger.warning(f"⚠️ Ошибка генерации QA: {e}")
    
    logger.info("")
    
    # ШАГ 2: Удаление старых коллекций
    logger.info("🗑️  ШАГ 2: Очистка старых коллекций")
    logger.info("-" * 80)
    try:
        rag_engine = RAGEngine()
        await rag_engine.initialize()
        
        collection_types = ["main", "architecture", "api", "models", "debug"]
        for ctype in collection_types:
            try:
                collection_name = f"kb_{project_name.replace('-', '_')}"
                if ctype != "main":
                    collection_name += f"_{ctype}"
                
                rag_engine.chroma_client.delete_collection(collection_name)
                logger.info(f"  ✓ Удалена коллекция: {collection_name}")
            except:
                pass  # Коллекция может не существовать
        
        logger.info("✅ Старые коллекции очищены")
    except Exception as e:
        logger.warning(f"⚠️ Ошибка очистки: {e}")
    
    logger.info("")
    
    # ШАГ 3: Индексация с улучшенными метаданными
    logger.info("📚 ШАГ 3: Индексация кода с расширенными метаданными")
    logger.info("-" * 80)
    
    project_indexer = SimpleProjectIndexer()
    project_indexer.load_config()
    python_indexer = PythonIndexer()
    markdown_indexer = MarkdownIndexer()
    rag_engine = RAGEngine()
    await rag_engine.initialize()
    
    stats = {
        'total_files': 0,
        'total_chunks': 0,
        'by_collection': {}
    }
    
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
            
            # Загрузка чанков в специализированные коллекции
            for chunk in chunks:
                doc_type = python_indexer._classify_doc_type(relative_path) if file_type == 'python' else 'documentation'
                
                # Определяем в какие коллекции добавить
                collections_to_add = ["main"]  # Всегда в main
                
                # architecture - для README, vision, высокоуровневых модулей
                if 'README' in relative_path or 'vision' in relative_path or 'doc/' in relative_path:
                    collections_to_add.append("architecture")
                
                # api - для роутов и API
                if doc_type in ['route', 'api', 'handler']:
                    collections_to_add.append("api")
                
                # models - для моделей БД
                if doc_type in ['model', 'schema'] or 'entities' in relative_path:
                    collections_to_add.append("models")
                
                # debug - для TODO/FIXME комментариев
                if 'TODO' in chunk['content'] or 'FIXME' in chunk['content']:
                    collections_to_add.append("debug")
                
                # Добавление в коллекции
                for coll_type in collections_to_add:
                    collection = rag_engine.get_collection(project_name, coll_type)
                    
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
                            'collection_type': coll_type,
                            'function_name': chunk.get('function_name'),
                            'parameters': chunk.get('parameters'),
                            'return_type': chunk.get('return_type'),
                            'chunk_id': chunk.get('chunk_id', hash(chunk['content'][:100]))
                        }
                    )
                    
                    stats['by_collection'][coll_type] = stats['by_collection'].get(coll_type, 0) + 1
                
                stats['total_chunks'] += 1
            
            # Прогресс каждые 10 файлов
            if stats['total_files'] % 10 == 0:
                logger.info(f"  📊 Обработано файлов: {stats['total_files']}, чанков: {stats['total_chunks']}")
        
        except Exception as e:
            logger.error(f"  ❌ Ошибка обработки {file_info.get('relative_path')}: {e}")
    
    logger.info(f"\n✅ Индексация завершена:")
    logger.info(f"   • Всего файлов: {stats['total_files']}")
    logger.info(f"   • Всего чанков: {stats['total_chunks']}")
    logger.info(f"\n📚 По коллекциям:")
    for coll_type, count in stats['by_collection'].items():
        logger.info(f"   • {coll_type}: {count} чанков")
    
    logger.info("")
    
    # ШАГ 4: Добавление сгенерированных QA пар
    logger.info("🎓 ШАГ 4: Добавление обучающих QA пар")
    logger.info("-" * 80)
    try:
        import json
        qa_file = Path("/tmp/generated_qa_pairs.json")
        if qa_file.exists():
            with open(qa_file, 'r', encoding='utf-8') as f:
                qa_pairs = json.load(f)
            
            for pair in qa_pairs:
                training_doc = f"""
ВОПРОС: {pair['question']}

ОТВЕТ: {pair['answer']}

---
Категория: {pair['metadata'].get('category', 'general')}
Файл: {pair['metadata'].get('file', 'N/A')}
"""
                await rag_engine.store_document(
                    project=project_name,
                    content=training_doc,
                    metadata={
                        'file': pair['metadata'].get('file', 'training_qa'),
                        'type': 'qa_pair',
                        'doc_type': 'training',
                        'project': project_name
                    }
                )
            
            logger.info(f"✅ Добавлено {len(qa_pairs)} обучающих пар")
        else:
            logger.warning("⚠️ Файл с QA парами не найден, пропускаем")
    except Exception as e:
        logger.warning(f"⚠️ Ошибка добавления QA: {e}")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("✅ ПЕРЕИНДЕКСАЦИЯ ЗАВЕРШЕНА")
    logger.info("=" * 80)
    
    return stats

if __name__ == "__main__":
    project = sys.argv[1] if len(sys.argv) > 1 else "staffprobot"
    asyncio.run(full_reindex(project))

