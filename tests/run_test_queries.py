#!/usr/bin/env python3
"""
Скрипт для тестирования качества ответов Project Brain
"""
import json
import requests
import time
from typing import Dict, List, Any
from datetime import datetime

API_URL = "http://localhost:8003/api/query"
PROJECT = "staffprobot"

def load_test_queries(file_path: str = "tests/test_queries.json") -> Dict[str, Any]:
    """Загрузка тестовых запросов"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_query(query: str) -> Dict[str, Any]:
    """Выполнение одного запроса"""
    try:
        response = requests.post(
            API_URL,
            json={"query": query, "project": PROJECT},
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"HTTP {response.status_code}",
                "answer": "",
                "sources": [],
                "processing_time": 0
            }
    except Exception as e:
        return {
            "error": str(e),
            "answer": "",
            "sources": [],
            "processing_time": 0
        }

def format_result(query: str, result: Dict[str, Any]) -> str:
    """Форматирование результата теста"""
    output = []
    output.append(f"\n{'='*80}")
    output.append(f"ВОПРОС: {query}")
    output.append(f"{'='*80}")
    
    if "error" in result:
        output.append(f"❌ ОШИБКА: {result['error']}")
    else:
        output.append(f"\n✅ ОТВЕТ ({result['processing_time']:.2f}с):")
        output.append(f"{result['answer'][:300]}...")
        
        output.append(f"\n📂 ИСТОЧНИКИ ({len(result['sources'])}):")
        for i, source in enumerate(result['sources'][:3], 1):
            output.append(f"  {i}. {source['file']} ({source.get('lines', 'N/A')})")
    
    return "\n".join(output)

def run_tests(limit_per_category: int = 2):
    """Запуск всех тестов"""
    print("🚀 Запуск тестирования Project Brain")
    print(f"⏰ Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 API URL: {API_URL}\n")
    
    # Загрузка тестовых запросов
    test_data = load_test_queries()
    
    results = []
    total_time = 0
    total_queries = 0
    
    for category_data in test_data["test_queries"]:
        category = category_data["category"]
        queries = category_data["queries"][:limit_per_category]
        
        print(f"\n{'='*80}")
        print(f"📁 КАТЕГОРИЯ: {category}")
        print(f"{'='*80}")
        
        for query in queries:
            print(f"\n⏳ Тестирую: {query[:60]}...")
            
            start_time = time.time()
            result = test_query(query)
            elapsed = time.time() - start_time
            
            total_queries += 1
            total_time += elapsed
            
            # Вывод результата
            formatted = format_result(query, result)
            print(formatted)
            
            # Сохранение результата
            results.append({
                "category": category,
                "query": query,
                "result": result,
                "elapsed": elapsed
            })
            
            # Пауза между запросами
            time.sleep(1)
    
    # Итоговая статистика
    print(f"\n{'='*80}")
    print(f"📊 ИТОГОВАЯ СТАТИСТИКА")
    print(f"{'='*80}")
    print(f"✅ Всего запросов: {total_queries}")
    print(f"⏱️  Общее время: {total_time:.2f}с")
    print(f"⚡ Среднее время: {total_time/total_queries:.2f}с")
    
    # Успешные/неуспешные
    successful = sum(1 for r in results if "error" not in r["result"])
    print(f"✅ Успешных: {successful}/{total_queries}")
    
    # Сохранение результатов
    output_file = f"tests/test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_queries": total_queries,
            "total_time": total_time,
            "avg_time": total_time/total_queries,
            "successful": successful,
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Результаты сохранены в: {output_file}")

if __name__ == "__main__":
    run_tests(limit_per_category=2)  # По 2 вопроса из каждой категории

