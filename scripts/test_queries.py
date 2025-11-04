#!/usr/bin/env python3
"""
Скрипт тестирования запросов к RAG
"""
import requests
import json
import sys
from datetime import datetime

API_URL = "http://192.168.2.107:8003/api/query"
TEST_FILE = "/app/tests/test_staffprobot_queries.json"

def test_query(query: str, category: str, expected_keywords: list):
    """Тестирование одного запроса"""
    try:
        response = requests.post(
            API_URL,
            json={"query": query, "project": "staffprobot"},
            timeout=30
        )
        
        if response.status_code != 200:
            return {
                "status": "error",
                "error": f"HTTP {response.status_code}"
            }
        
        data = response.json()
        answer = data.get("answer", "")
        sources = data.get("sources", [])
        
        # Проверка keywords
        found_keywords = [kw for kw in expected_keywords if kw.lower() in answer.lower()]
        keyword_score = len(found_keywords) / len(expected_keywords) if expected_keywords else 0
        
        return {
            "status": "success",
            "answer_length": len(answer),
            "sources_count": len(sources),
            "found_keywords": found_keywords,
            "keyword_score": keyword_score,
            "answer_preview": answer[:200] + "..." if len(answer) > 200 else answer
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def main():
    # Загрузка тестовых вопросов
    with open(TEST_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    queries = data["test_queries"]
    
    print("=" * 80)
    print(f"🧪 Тестирование RAG для StaffProBot")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📋 Всего вопросов: {len(queries)}")
    print("=" * 80)
    print()
    
    results = []
    
    for i, q in enumerate(queries[:10], 1):  # Первые 10 вопросов
        print(f"\n{'─' * 80}")
        print(f"[{i}/{len(queries[:10])}] {q['category']} ({q['difficulty']})")
        print(f"❓ {q['query']}")
        print()
        
        result = test_query(
            q['query'],
            q['category'],
            q['expected_keywords']
        )
        
        if result['status'] == 'success':
            print(f"✅ Успешно")
            print(f"   📝 Длина ответа: {result['answer_length']} символов")
            print(f"   📚 Источников: {result['sources_count']}")
            print(f"   🎯 Keywords: {result['keyword_score']*100:.0f}% ({len(result['found_keywords'])}/{len(q['expected_keywords'])})")
            if result['found_keywords']:
                print(f"   ✓ Найдены: {', '.join(result['found_keywords'][:5])}")
            print(f"\n   💬 Превью: {result['answer_preview']}")
        else:
            print(f"❌ Ошибка: {result['error']}")
        
        results.append({
            "query": q,
            "result": result
        })
    
    # Статистика
    print("\n" + "=" * 80)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 80)
    
    successful = [r for r in results if r['result']['status'] == 'success']
    print(f"✅ Успешных запросов: {len(successful)}/{len(results)}")
    
    if successful:
        avg_sources = sum(r['result']['sources_count'] for r in successful) / len(successful)
        avg_keywords = sum(r['result']['keyword_score'] for r in successful) / len(successful)
        
        print(f"📚 Среднее кол-во источников: {avg_sources:.1f}")
        print(f"🎯 Средний keyword score: {avg_keywords*100:.0f}%")
    
    print("=" * 80)

if __name__ == "__main__":
    main()

