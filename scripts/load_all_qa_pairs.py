#!/usr/bin/env python3
"""
Загрузчик всех QA пар в базу знаний
Объединяет все источники QA пар и загружает в ChromaDB
"""
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, '/app')

from backend.rag.engine import RAGEngine

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class QALoader:
    def __init__(self):
        self.rag_engine = RAGEngine()
        self.qa_pairs = []
        
    def load_all_qa_sources(self) -> List[Dict[str, Any]]:
        """Загрузка QA пар из всех источников"""
        logger.info("📚 Загрузка QA пар из всех источников...")
        
        # 1. Загружаем существующие QA пары
        existing_pairs = self._load_existing_qa_pairs()
        self.qa_pairs.extend(existing_pairs)
        logger.info(f"✅ Существующие QA пары: {len(existing_pairs)}")
        
        # 2. Загружаем QA пары из графа зависимостей
        graph_pairs = self._load_graph_qa_pairs()
        self.qa_pairs.extend(graph_pairs)
        logger.info(f"✅ QA пары из графа: {len(graph_pairs)}")
        
        # 3. Загружаем массовые QA пары
        massive_pairs = self._load_massive_qa_pairs()
        self.qa_pairs.extend(massive_pairs)
        logger.info(f"✅ Массовые QA пары: {len(massive_pairs)}")
        
        # 4. Загружаем ЦЕЛЕВЫЕ QA пары (НОВОЕ!)
        targeted_pairs = self._load_targeted_qa_pairs()
        self.qa_pairs.extend(targeted_pairs)
        logger.info(f"✅ Целевые QA пары: {len(targeted_pairs)}")
        
        # 5. Загружаем СУПЕР-ДЕТАЛЬНЫЕ QA пары (НОВОЕ!)
        super_pairs = self._load_super_detailed_qa_pairs()
        self.qa_pairs.extend(super_pairs)
        logger.info(f"✅ Супер-детальные QA пары: {len(super_pairs)}")
        
        # 6. Загружаем QA пары из тестов
        test_pairs = self._load_test_qa_pairs()
        self.qa_pairs.extend(test_pairs)
        logger.info(f"✅ Тестовые QA пары: {len(test_pairs)}")
        
        # Удаляем дубликаты
        unique_pairs = self._remove_duplicates()
        logger.info(f"📊 ВСЕГО уникальных QA пар: {len(unique_pairs)}")
        
        return unique_pairs
    
    def _load_existing_qa_pairs(self) -> List[Dict[str, Any]]:
        """Загрузка существующих QA пар"""
        try:
            with open("/tmp/generated_qa_pairs.json", 'r', encoding='utf-8') as f:
                pairs = json.load(f)
            logger.info(f"📄 Загружено из generated_qa_pairs.json: {len(pairs)}")
            return pairs
        except FileNotFoundError:
            logger.warning("⚠️ Файл generated_qa_pairs.json не найден")
            return []
    
    def _load_graph_qa_pairs(self) -> List[Dict[str, Any]]:
        """Загрузка QA пар из графа зависимостей"""
        try:
            with open("/tmp/graph_qa_pairs.json", 'r', encoding='utf-8') as f:
                pairs = json.load(f)
            logger.info(f"🔗 Загружено из graph_qa_pairs.json: {len(pairs)}")
            return pairs
        except FileNotFoundError:
            logger.warning("⚠️ Файл graph_qa_pairs.json не найден")
            return []
    
    def _load_massive_qa_pairs(self) -> List[Dict[str, Any]]:
        """Загрузка массовых QA пар"""
        try:
            with open("/tmp/massive_qa_pairs.json", 'r', encoding='utf-8') as f:
                pairs = json.load(f)
            logger.info(f"📦 Загружено из massive_qa_pairs.json: {len(pairs)}")
            return pairs
        except FileNotFoundError:
            logger.warning("⚠️ Файл massive_qa_pairs.json не найден")
            return []
    
    def _load_targeted_qa_pairs(self) -> List[Dict[str, Any]]:
        """Загрузка целевых QA пар"""
        try:
            with open("/tmp/targeted_qa_pairs.json", 'r', encoding='utf-8') as f:
                pairs = json.load(f)
            logger.info(f"🎯 Загружено из targeted_qa_pairs.json: {len(pairs)}")
            return pairs
        except FileNotFoundError:
            logger.warning("⚠️ Файл targeted_qa_pairs.json не найден")
            return []
    
    def _load_super_detailed_qa_pairs(self) -> List[Dict[str, Any]]:
        """Загрузка супер-детальных QA пар"""
        try:
            with open("/tmp/super_detailed_qa_pairs.json", 'r', encoding='utf-8') as f:
                pairs = json.load(f)
            logger.info(f"🚀 Загружено из super_detailed_qa_pairs.json: {len(pairs)}")
            return pairs
        except FileNotFoundError:
            logger.warning("⚠️ Файл super_detailed_qa_pairs.json не найден")
            return []
    
    def _load_test_qa_pairs(self) -> List[Dict[str, Any]]:
        """Загрузка тестовых QA пар"""
        try:
            with open("/app/tests/test_staffprobot_queries.json", 'r', encoding='utf-8') as f:
                test_data = json.load(f)
            
            pairs = []
            for item in test_data:
                # Проверяем, что item - это словарь
                if isinstance(item, dict) and "question" in item:
                    pairs.append({
                        "question": item["question"],
                        "answer": item.get("expected_answer", "Ответ не предоставлен"),
                        "metadata": {
                            "category": item.get("category", "test"),
                            "difficulty": item.get("difficulty", "medium"),
                            "topic": item.get("topic", "general")
                        }
                    })
            
            logger.info(f"🧪 Загружено из test_staffprobot_queries.json: {len(pairs)}")
            return pairs
        except FileNotFoundError:
            logger.warning("⚠️ Файл test_staffprobot_queries.json не найден")
            return []
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки тестовых QA пар: {e}")
            return []
    
    def _remove_duplicates(self) -> List[Dict[str, Any]]:
        """Удаление дубликатов по вопросу"""
        seen_questions = set()
        unique_pairs = []
        
        for pair in self.qa_pairs:
            question = pair["question"].lower().strip()
            if question not in seen_questions:
                seen_questions.add(question)
                unique_pairs.append(pair)
        
        logger.info(f"🔄 Удалено дубликатов: {len(self.qa_pairs) - len(unique_pairs)}")
        return unique_pairs
    
    async def store_qa_pairs(self, pairs: List[Dict[str, Any]]) -> int:
        """Сохранение QA пар в ChromaDB"""
        logger.info(f"💾 Сохранение {len(pairs)} QA пар в ChromaDB...")
        
        stored_count = 0
        for i, pair in enumerate(pairs):
            try:
                # Создаем документ для ChromaDB
                doc_id = f"qa_pair_{i}_{hash(pair['question'])}"
                
                # Объединяем вопрос и ответ для лучшего поиска
                content = f"Вопрос: {pair['question']}\n\nОтвет: {pair['answer']}"
                
                # Подготавливаем метаданные (БЕЗ answer - он слишком большой!)
                metadata = {
                    "type": "qa_pair",
                    "question": pair["question"][:500],  # Ограничиваем размер
                    "source": "qa_training",
                    "chunk_id": f"qa_{i}_{hash(pair['question'])}"  # УНИКАЛЬНЫЙ ID!
                }
                
                # Добавляем дополнительные метаданные (ТОЛЬКО простые типы!)
                if "metadata" in pair:
                    for key, value in pair["metadata"].items():
                        # Сохраняем только str, int, float, bool
                        if isinstance(value, (str, int, float, bool)):
                            # Ограничиваем длину строк
                            if isinstance(value, str):
                                metadata[key] = value[:200]
                            else:
                                metadata[key] = value
                
                # chunk_id остается уникальным
                metadata["chunk_id"] = f"qa_{i}_{hash(pair['question'])}"
                
                # Сохраняем в ChromaDB (ASYNC!)
                await self.rag_engine.store_document(
                    project="staffprobot",
                    content=content,
                    metadata=metadata
                )
                
                stored_count += 1
                
                if stored_count % 100 == 0:
                    logger.info(f"  💾 Сохранено {stored_count}/{len(pairs)} QA пар")
                
            except Exception as e:
                logger.error(f"❌ Ошибка сохранения QA пары {i}: {e}")
        
        logger.info(f"✅ Успешно сохранено {stored_count} QA пар")
        return stored_count
    
    def generate_summary_report(self, pairs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Генерация отчета по QA парам"""
        categories = {}
        difficulties = {}
        sources = {}
        
        for pair in pairs:
            metadata = pair.get("metadata", {})
            
            # Категории
            category = metadata.get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1
            
            # Сложность
            difficulty = metadata.get("difficulty", "unknown")
            difficulties[difficulty] = difficulties.get(difficulty, 0) + 1
            
            # Источники
            source = metadata.get("source", "unknown")
            sources[source] = sources.get(source, 0) + 1
        
        return {
            "total_pairs": len(pairs),
            "categories": categories,
            "difficulties": difficulties,
            "sources": sources
        }

async def main():
    """Основная функция загрузки QA пар"""
    logger.info("🚀 Начинаю загрузку всех QA пар в базу знаний...")
    
    loader = QALoader()
    
    # Загружаем все QA пары
    all_pairs = loader.load_all_qa_sources()
    
    if not all_pairs:
        logger.error("❌ Не найдено QA пар для загрузки!")
        return
    
    # Генерируем отчет
    report = loader.generate_summary_report(all_pairs)
    
    logger.info("\n📊 ОТЧЕТ ПО QA ПАРАМ:")
    logger.info(f"Всего пар: {report['total_pairs']}")
    
    logger.info("\n📂 По категориям:")
    for category, count in sorted(report['categories'].items()):
        logger.info(f"  • {category}: {count}")
    
    logger.info("\n🎯 По сложности:")
    for difficulty, count in sorted(report['difficulties'].items()):
        logger.info(f"  • {difficulty}: {count}")
    
    logger.info("\n📚 По источникам:")
    for source, count in sorted(report['sources'].items()):
        logger.info(f"  • {source}: {count}")
    
    # Сохраняем QA пары в ChromaDB (ASYNC!)
    stored_count = await loader.store_qa_pairs(all_pairs)
    
    logger.info(f"\n🎉 ЗАГРУЗКА ЗАВЕРШЕНА!")
    logger.info(f"✅ Загружено {stored_count} QA пар в базу знаний")
    logger.info(f"📈 База знаний теперь содержит {stored_count} обучающих примеров")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
