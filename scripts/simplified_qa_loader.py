#!/usr/bin/env python3
"""
Упрощенный загрузчик QA пар
Без полного кода в metadata - только ссылки
"""
import sys
import json
import logging
sys.path.insert(0, '/app')

from backend.rag.engine import RAGEngine

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def load_simplified_qa():
    """Загрузка упрощенных QA пар"""
    logger.info("🚀 УПРОЩЕННАЯ ЗАГРУЗКА QA ПАР")
    
    # Загружаем все QA пары
    all_pairs = []
    
    files = [
        ('/tmp/targeted_qa_pairs.json', 'targeted'),
        ('/tmp/super_detailed_qa_pairs.json', 'super'),
        ('/tmp/generated_qa_pairs.json', 'generated'),
        ('/tmp/graph_qa_pairs.json', 'graph'),
        ('/tmp/massive_qa_pairs.json', 'massive'),
    ]
    
    for file_path, source in files:
        try:
            with open(file_path, 'r') as f:
                pairs = json.load(f)
                logger.info(f"✅ {source}: {len(pairs)} пар")
                all_pairs.extend(pairs)
        except:
            logger.warning(f"⚠️ Файл {source} не найден")
    
    logger.info(f"\n📊 ВСЕГО загружено: {len(all_pairs)} QA пар")
    
    # Удаляем дубликаты
    seen = set()
    unique_pairs = []
    for pair in all_pairs:
        q = pair['question'].lower().strip()
        if q not in seen:
            seen.add(q)
            unique_pairs.append(pair)
    
    logger.info(f"📊 Уникальных: {len(unique_pairs)} QA пар")
    
    # Инициализируем RAG
    engine = RAGEngine()
    await engine.initialize()
    
    # Загружаем батчами
    batch_size = 500
    total_stored = 0
    
    for batch_idx in range(0, len(unique_pairs), batch_size):
        batch = unique_pairs[batch_idx:batch_idx + batch_size]
        
        logger.info(f"\n💾 Батч {batch_idx//batch_size + 1}/{(len(unique_pairs)-1)//batch_size + 1}: {len(batch)} пар")
        
        for i, pair in enumerate(batch):
            try:
                # УПРОЩЕННЫЙ content (без огромного кода)
                content = f"Вопрос: {pair['question']}\nОтвет: {pair['answer'][:500]}"
                
                # МИНИМАЛЬНЫЕ metadata
                metadata = {
                    "type": "qa_pair",
                    "question": pair['question'][:200],
                    "chunk_id": f"qa_{batch_idx + i}_{abs(hash(pair['question']))}"
                }
                
                # Добавляем только простые поля из дополнительных метаданных
                if "metadata" in pair:
                    for key in ['file', 'function', 'class', 'endpoint', 'line']:
                        if key in pair['metadata']:
                            val = pair['metadata'][key]
                            if isinstance(val, str):
                                metadata[key] = val[:100]
                            elif isinstance(val, int):
                                metadata[key] = str(val)
                
                # Сохраняем
                await engine.store_document(
                    project='staffprobot',
                    content=content,
                    metadata=metadata
                )
                
                total_stored += 1
                
            except Exception as e:
                logger.error(f"❌ Ошибка пары {batch_idx + i}: {str(e)[:100]}")
        
        logger.info(f"  ✅ Сохранено {len(batch)} из батча. Всего: {total_stored}")
    
    logger.info(f"\n🎉 ЗАГРУЗКА ЗАВЕРШЕНА!")
    logger.info(f"✅ Успешно сохранено: {total_stored} QA пар")

if __name__ == "__main__":
    import asyncio
    asyncio.run(load_simplified_qa())

