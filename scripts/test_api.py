#!/usr/bin/env python3
"""
Скрипт для тестирования Project Brain API
"""
import requests
import json
import time
import sys

API_BASE = "http://localhost:8001"

def test_health():
    """Тест проверки здоровья API"""
    print("🔍 Тестирование /health...")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_query():
    """Тест запроса к AI"""
    print("🤖 Тестирование /api/query...")
    try:
        payload = {
            "query": "Как работает система отмены смен?",
            "project": "staffprobot",
            "max_tokens": 500
        }
        
        response = requests.post(
            f"{API_BASE}/api/query",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Query test passed")
            print(f"📝 Ответ: {data['answer'][:200]}...")
            print(f"📊 Источники: {len(data.get('sources', []))}")
            print(f"⏱️  Время обработки: {data.get('processing_time', 0):.2f}с")
            return True
        else:
            print(f"❌ Query test failed: {response.status_code}")
            print(f"📄 Ответ: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Query test error: {e}")
        return False

def test_projects():
    """Тест получения списка проектов"""
    print("📁 Тестирование /api/projects...")
    try:
        response = requests.get(f"{API_BASE}/api/projects", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Projects test passed")
            print(f"📊 Проектов: {len(data)}")
            for project in data:
                print(f"  - {project['name']}: {project.get('description', 'No description')}")
            return True
        else:
            print(f"❌ Projects test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Projects test error: {e}")
        return False

def test_stats():
    """Тест получения статистики"""
    print("📊 Тестирование /api/stats...")
    try:
        response = requests.get(f"{API_BASE}/api/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Stats test passed")
            print(f"📊 Общая статистика:")
            print(f"  - Проектов: {data.get('total_projects', 0)}")
            print(f"  - Чанков: {data.get('total_chunks', 0)}")
            print(f"  - Файлов: {data.get('total_files', 0)}")
            return True
        else:
            print(f"❌ Stats test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Stats test error: {e}")
        return False

def test_context_rules():
    """Тест получения контекстных правил"""
    print("📋 Тестирование /api/context-rules...")
    try:
        params = {
            "file": "apps/web/routes/owner.py",
            "role": "owner"
        }
        response = requests.get(f"{API_BASE}/api/context-rules", params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Context rules test passed")
            print(f"📋 Правил: {data.get('rules_count', 0)}")
            print(f"🔢 Токенов: {data.get('estimated_tokens', 0)}")
            return True
        else:
            print(f"❌ Context rules test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Context rules test error: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🧪 Запуск тестов Project Brain API")
    print("=" * 50)
    
    tests = [
        test_health,
        test_projects,
        test_stats,
        test_context_rules,
        test_query
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except KeyboardInterrupt:
            print("\n⏹️  Тестирование прервано пользователем")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Неожиданная ошибка в тесте: {e}")
            print()
    
    print("=" * 50)
    print(f"📊 Результаты: {passed}/{total} тестов прошли")
    
    if passed == total:
        print("🎉 Все тесты прошли успешно!")
        sys.exit(0)
    else:
        print("❌ Некоторые тесты не прошли")
        sys.exit(1)

if __name__ == "__main__":
    main()
