#!/usr/bin/env python3
"""
Загрузка сгенерированных QA пар в базу знаний
"""
import asyncio
import json
import sys
import logging
from pathlib import Path

sys.path.insert(0, '/app')

from backend.rag.engine import RAGEngine

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def load_qa_pairs(qa_file: str = "/tmp/generated_qa_pairs.json", project: str = "staffprobot"):
    """Загрузка QA пар в базу знаний"""
    logger.info(f"📚 Загрузка QA пар из {qa_file}")
    
    # Загрузка файла
    with open(qa_file, 'r', encoding='utf-8') as f:
        qa_pairs = json.load(f)
    
    logger.info(f"📊 Всего пар: {len(qa_pairs)}")
    
    # Инициализация RAG
    rag_engine = RAGEngine()
    await rag_engine.initialize()
    
    # Добавление пар
    added = 0
    for i, pair in enumerate(qa_pairs, 1):
        try:
            # Форматирование QA пары для лучшего поиска
            training_doc = f"""ВОПРОС: {pair['question']}

ОТВЕТ: {pair['answer']}

---
Категория: {pair['metadata'].get('category', 'general')}
Файл: {pair['metadata'].get('file', 'N/A')}
Сложность: {pair['metadata'].get('difficulty', 'medium')}"""

            await rag_engine.store_document(
                project=project,
                content=training_doc,
                metadata={
                    'file': pair['metadata'].get('file', 'training_qa'),
                    'type': 'qa_pair',
                    'doc_type': 'training',
                    'category': pair['metadata'].get('category', 'general'),
                    'project': project
                }
            )
            
            added += 1
            
            # Прогресс каждые 50 пар
            if i % 50 == 0:
                logger.info(f"  ✓ Добавлено: {i}/{len(qa_pairs)}")
        
        except Exception as e:
            logger.error(f"  ✗ Ошибка добавления пары {i}: {e}")
    
    logger.info(f"\n✅ Успешно добавлено: {added}/{len(qa_pairs)} пар")

if __name__ == "__main__":
    project = sys.argv[1] if len(sys.argv) > 1 else "staffprobot"
    asyncio.run(load_qa_pairs(project=project))

