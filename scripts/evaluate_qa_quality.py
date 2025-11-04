#!/usr/bin/env python3
"""
Система оценки качества RAG ответов
Метрики: line_numbers, file_path, code_snippet, keywords
"""
import json
import re
import sys
from pathlib import Path
import requests
from typing import Dict, Any, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QAQualityEvaluator:
    def __init__(self, api_url: str = "http://192.168.2.107:8003/api/query"):
        self.api_url = api_url
        self.results = []
        
    def evaluate_answer(self, question: str, answer: str, expected_keywords: List[str]) -> Dict[str, Any]:
        """Оценка качества одного ответа"""
        metrics = {}
        
        # 1. has_line_numbers: содержит ли ответ "строки XX-YY" или "📍 Строки: XX-YY" (вес 40%)
        line_pattern = r'строк[аеи]?:?\s+\d+-\d+|строк[аеи]?\s+\d+|line[s]?\s+\d+-\d+|📍\s*[Сс]трок[аеи]?:?\s+\d+-\d+'
        has_lines = bool(re.search(line_pattern, answer, re.IGNORECASE))
        metrics['has_line_numbers'] = 1.0 if has_lines else 0.0
        
        # 2. has_file_path: содержит ли путь к файлу (вес 20%)
        file_pattern = r'[\w/]+\.py|[\w/]+\.md'
        has_file = bool(re.search(file_pattern, answer))
        metrics['has_file_path'] = 1.0 if has_file else 0.0
        
        # 3. has_code_snippet: содержит ли блок кода (вес 20%)
        code_pattern = r'```[\s\S]*?```'
        has_code = bool(re.search(code_pattern, answer))
        metrics['has_code_snippet'] = 1.0 if has_code else 0.0
        
        # 4. keyword_match: совпадение ключевых слов из вопроса (вес 20%)
        if expected_keywords:
            answer_lower = answer.lower()
            matched_keywords = [kw for kw in expected_keywords if kw.lower() in answer_lower]
            metrics['keyword_match'] = len(matched_keywords) / len(expected_keywords)
        else:
            metrics['keyword_match'] = 1.0
        
        # Общий score с весами
        total_score = (
            metrics['has_line_numbers'] * 0.40 +
            metrics['has_file_path'] * 0.20 +
            metrics['has_code_snippet'] * 0.20 +
            metrics['keyword_match'] * 0.20
        )
        metrics['total_score'] = total_score
        
        return metrics
    
    def test_query(self, question: str, project: str = "staffprobot") -> Dict[str, Any]:
        """Выполнение запроса к RAG"""
        try:
            response = requests.post(
                self.api_url,
                json={"query": question, "project": project},
                timeout=30
            )
            
            if response.status_code != 200:
                return {"error": f"HTTP {response.status_code}"}
            
            data = response.json()
            return {
                "answer": data.get("answer", ""),
                "sources": data.get("sources", []),
                "sources_count": len(data.get("sources", []))
            }
        
        except Exception as e:
            return {"error": str(e)}
    
    def run_evaluation(self, test_file: str = "/app/tests/test_staffprobot_queries.json"):
        """Запуск оценки на тестовом наборе"""
        logger.info("📊 Начало оценки качества RAG")
        
        # Загрузка тестовых вопросов
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
            test_queries = test_data.get("test_queries", [])
        except Exception as e:
            logger.error(f"Ошибка загрузки тестов: {e}")
            return
        
        logger.info(f"📋 Загружено {len(test_queries)} тестовых вопросов\n")
        
        # Оценка каждого вопроса
        for i, query in enumerate(test_queries, 1):
            logger.info(f"[{i}/{len(test_queries)}] {query['category']} ({query['difficulty']})")
            logger.info(f"❓ {query['query']}")
            
            # Выполнение запроса
            result = self.test_query(query['query'])
            
            if "error" in result:
                logger.error(f"❌ Ошибка: {result['error']}\n")
                self.results.append({
                    "query": query,
                    "error": result["error"],
                    "metrics": None
                })
                continue
            
            # Оценка ответа
            metrics = self.evaluate_answer(
                query['query'],
                result['answer'],
                query.get('expected_keywords', [])
            )
            
            # Вывод метрик
            logger.info(f"📝 Ответ ({len(result['answer'])} симв.)")
            logger.info(f"📚 Источников: {result['sources_count']}")
            logger.info(f"📊 Метрики:")
            logger.info(f"   • Line numbers: {metrics['has_line_numbers']*100:.0f}%")
            logger.info(f"   • File path: {metrics['has_file_path']*100:.0f}%")
            logger.info(f"   • Code snippet: {metrics['has_code_snippet']*100:.0f}%")
            logger.info(f"   • Keywords: {metrics['keyword_match']*100:.0f}%")
            logger.info(f"   ⭐ TOTAL: {metrics['total_score']*100:.0f}%")
            
            # Показать превью ответа
            preview = result['answer'][:150].replace('\n', ' ')
            logger.info(f"   💬 {preview}...\n")
            
            self.results.append({
                "query": query,
                "result": result,
                "metrics": metrics
            })
        
        # Итоговая статистика
        self._print_summary()
    
    def _print_summary(self):
        """Вывод итоговой статистики"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 ИТОГОВАЯ СТАТИСТИКА")
        logger.info("=" * 80)
        
        successful = [r for r in self.results if r.get('metrics')]
        failed = [r for r in self.results if not r.get('metrics')]
        
        logger.info(f"✅ Успешных запросов: {len(successful)}/{len(self.results)}")
        if failed:
            logger.info(f"❌ Ошибок: {len(failed)}")
        
        if not successful:
            logger.warning("⚠️ Нет успешных результатов для анализа")
            return
        
        # Агрегированные метрики
        avg_metrics = {
            'has_line_numbers': sum(r['metrics']['has_line_numbers'] for r in successful) / len(successful),
            'has_file_path': sum(r['metrics']['has_file_path'] for r in successful) / len(successful),
            'has_code_snippet': sum(r['metrics']['has_code_snippet'] for r in successful) / len(successful),
            'keyword_match': sum(r['metrics']['keyword_match'] for r in successful) / len(successful),
            'total_score': sum(r['metrics']['total_score'] for r in successful) / len(successful)
        }
        
        logger.info(f"\n📈 Средние метрики:")
        logger.info(f"   • Has Line Numbers: {avg_metrics['has_line_numbers']*100:.1f}% {'✅' if avg_metrics['has_line_numbers'] >= 0.85 else '❌'} (цель: >85%)")
        logger.info(f"   • Has File Path: {avg_metrics['has_file_path']*100:.1f}% {'✅' if avg_metrics['has_file_path'] >= 0.95 else '❌'} (цель: >95%)")
        logger.info(f"   • Has Code Snippet: {avg_metrics['has_code_snippet']*100:.1f}% {'✅' if avg_metrics['has_code_snippet'] >= 0.80 else '❌'} (цель: >80%)")
        logger.info(f"   • Keyword Match: {avg_metrics['keyword_match']*100:.1f}% {'✅' if avg_metrics['keyword_match'] >= 0.90 else '❌'} (цель: >90%)")
        logger.info(f"   ⭐ TOTAL SCORE: {avg_metrics['total_score']*100:.1f}%")
        
        # Проблемные вопросы (score < 50%)
        problematic = [r for r in successful if r['metrics']['total_score'] < 0.5]
        if problematic:
            logger.info(f"\n⚠️ Проблемные вопросы ({len(problematic)}):")
            for r in problematic[:5]:  # Показать первые 5
                logger.info(f"   • [{r['metrics']['total_score']*100:.0f}%] {r['query']['query'][:60]}...")
        
        # Категории по качеству
        excellent = [r for r in successful if r['metrics']['total_score'] >= 0.85]
        good = [r for r in successful if 0.70 <= r['metrics']['total_score'] < 0.85]
        fair = [r for r in successful if 0.50 <= r['metrics']['total_score'] < 0.70]
        poor = [r for r in successful if r['metrics']['total_score'] < 0.50]
        
        logger.info(f"\n📊 Распределение по качеству:")
        logger.info(f"   • Отлично (>85%): {len(excellent)} ({len(excellent)/len(successful)*100:.1f}%)")
        logger.info(f"   • Хорошо (70-85%): {len(good)} ({len(good)/len(successful)*100:.1f}%)")
        logger.info(f"   • Удовлетворительно (50-70%): {len(fair)} ({len(fair)/len(successful)*100:.1f}%)")
        logger.info(f"   • Плохо (<50%): {len(poor)} ({len(poor)/len(successful)*100:.1f}%)")
        
        logger.info("=" * 80)
        
        # Сохранение результатов
        self._save_results()
    
    def _save_results(self):
        """Сохранение результатов оценки"""
        output_file = "/tmp/qa_evaluation_results.json"
        
        # Подготовка данных для сохранения
        output_data = {
            "total_queries": len(self.results),
            "successful": len([r for r in self.results if r.get('metrics')]),
            "failed": len([r for r in self.results if not r.get('metrics')]),
            "results": []
        }
        
        for r in self.results:
            output_data["results"].append({
                "question": r['query']['query'],
                "category": r['query']['category'],
                "difficulty": r['query']['difficulty'],
                "metrics": r.get('metrics'),
                "answer_preview": r.get('result', {}).get('answer', '')[:200] if r.get('result') else None,
                "sources_count": r.get('result', {}).get('sources_count', 0) if r.get('result') else 0
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n💾 Результаты сохранены в {output_file}")

def main():
    evaluator = QAQualityEvaluator()
    evaluator.run_evaluation()

if __name__ == "__main__":
    main()

