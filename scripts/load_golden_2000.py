#!/usr/bin/env python3
"""
ЗОЛОТОЙ НАБОР - 2000 лучших QA пар
Фильтруем только ВАЖНЫЕ темы
"""
import json
import sys
sys.path.insert(0, '/app')

from backend.rag.engine import RAGEngine
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def load_golden_set():
    """Загрузка золотого набора из 2000 лучших QA пар"""
    logger.info("🏆 ЗАГРУЗКА ЗОЛОТОГО НАБОРА (2000 QA пар)")
    
    all_pairs = []
    
    # 1. Базовые 474 качественных
    try:
        with open('/tmp/generated_qa_pairs.json', 'r') as f:
            generated = json.load(f)
        all_pairs.extend(generated)
        logger.info(f"✅ Базовые: {len(generated)} пар")
    except:
        logger.warning("⚠️ generated_qa_pairs.json не найден")
    
    # 2. Лучшие из targeted (только routes, services, models, handlers)
    try:
        with open('/tmp/targeted_qa_pairs.json', 'r') as f:
            targeted = json.load(f)
        
        # Фильтруем только важные
        important = []
        for pair in targeted:
            meta = pair.get('metadata', {})
            file = meta.get('file', '')
            
            # Только важные файлы
            if any(keyword in file for keyword in ['routes/', 'services/', 'entities/', 'handlers/']):
                important.append(pair)
        
        logger.info(f"✅ Целевые (отфильтровано): {len(important)} из {len(targeted)}")
        all_pairs.extend(important[:1526])  # Берём 1526 чтобы было ровно 2000
    except:
        logger.warning("⚠️ targeted_qa_pairs.json не найден")
    
    logger.info(f"\n📊 ИТОГО для загрузки: {len(all_pairs)} QA пар")
    
    # Инициализация
    engine = RAGEngine()
    await engine.initialize()
    
    # Загрузка
    stored = 0
    for i, pair in enumerate(all_pairs):
        try:
            # Полный ответ
            content = f"Вопрос: {pair['question']}\n\nОтвет: {pair['answer']}"
            
            # Минимальные метаданные
            metadata = {
                'type': 'qa_pair',
                'question': pair['question'][:200],
                'chunk_id': f'golden_{i}_{abs(hash(pair["question"]))}'
            }
            
            # Добавляем file и lines если есть
            if 'metadata' in pair:
                for key in ['file', 'lines', 'function', 'class', 'endpoint']:
                    if key in pair['metadata']:
                        val = pair['metadata'][key]
                        if isinstance(val, str):
                            metadata[key] = val[:100]
            
            await engine.store_document('staffprobot', content, metadata)
            stored += 1
            
            if stored % 200 == 0:
                logger.info(f"  💾 Загружено {stored}/{len(all_pairs)}")
        
        except Exception as e:
            logger.error(f"❌ Ошибка {i}: {str(e)[:80]}")
    
    logger.info(f"\n🎉 ГОТОВО! Загружено {stored} QA пар")

if __name__ == "__main__":
    asyncio.run(load_golden_set())

