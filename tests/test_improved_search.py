#!/usr/bin/env python3
"""
Тестирование улучшенного поиска с doc_type и умной приоритизацией
"""
import requests
import json
from datetime import datetime

API_URL = "http://localhost:8003/api/query"

# Тестовые запросы для проверки точности
TEST_QUERIES = [
    {
        "category": "how_to (должны находить роуты)",
        "queries": [
            "что нужно сделать, чтобы создать объект?",
            "как открыть смену?",
            "как добавить нового сотрудника?",
            "как изменить настройки объекта?",
        ],
        "expected_doc_types": ["route", "handler", "api"],
        "not_expected": ["model"]  # Модели не должны быть первыми
    },
    {
        "category": "structure (должны находить модели)",
        "queries": [
            "какие поля в модели User?",
            "какая структура таблицы shifts?",
            "какие атрибуты у объекта Object?",
        ],
        "expected_doc_types": ["model", "schema"],
        "not_expected": ["route"]
    },
    {
        "category": "api (должны находить роуты)",
        "queries": [
            "какие API endpoints для работы с объектами?",
            "какие роуты для календаря?",
        ],
        "expected_doc_types": ["route", "api"],
        "not_expected": []
    }
]

def test_query(query: str) -> dict:
    """Выполнить запрос к API"""
    try:
        response = requests.post(
            API_URL,
            json={"query": query, "project": "staffprobot"},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def analyze_results(result: dict, expected_types: list, not_expected: list) -> dict:
    """Анализ качества результатов"""
    analysis = {
        "found_expected": False,
        "found_unexpected": False,
        "first_doc_type": None,
        "doc_types": []
    }
    
    sources = result.get("sources", [])
    if not sources:
        return analysis
    
    for source in sources:
        # В метаданных теперь должен быть doc_type
        # Но API может не передавать его, так что проверим по файлу
        file_path = source.get("file", "").lower()
        
        # Определяем doc_type по пути файла
        if "routes" in file_path or "routers" in file_path:
            doc_type = "route"
        elif "handlers" in file_path:
            doc_type = "handler"
        elif "api" in file_path and "domain" not in file_path:
            doc_type = "api"
        elif "models" in file_path or "entities" in file_path:
            doc_type = "model"
        elif "services" in file_path:
            doc_type = "service"
        else:
            doc_type = "other"
        
        analysis["doc_types"].append(doc_type)
    
    # Первый результат
    if analysis["doc_types"]:
        analysis["first_doc_type"] = analysis["doc_types"][0]
        
        # Проверка ожидаемых типов
        if analysis["first_doc_type"] in expected_types:
            analysis["found_expected"] = True
        
        # Проверка нежелательных типов
        if analysis["first_doc_type"] in not_expected:
            analysis["found_unexpected"] = True
    
    return analysis

def run_tests():
    """Запуск всех тестов"""
    print("🧪 Тестирование улучшенного поиска")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    total_tests = 0
    passed_tests = 0
    
    for test_category in TEST_QUERIES:
        category = test_category["category"]
        expected_types = test_category["expected_doc_types"]
        not_expected = test_category["not_expected"]
        
        print(f"\n{'='*80}")
        print(f"📁 КАТЕГОРИЯ: {category}")
        print(f"✅ Ожидаем: {', '.join(expected_types)}")
        if not_expected:
            print(f"❌ НЕ ожидаем: {', '.join(not_expected)}")
        print(f"{'='*80}\n")
        
        for query in test_category["queries"]:
            total_tests += 1
            print(f"❓ Вопрос: {query}")
            
            # Выполняем запрос
            result = test_query(query)
            
            if "error" in result:
                print(f"   ❌ ОШИБКА: {result['error']}\n")
                continue
            
            # Анализируем результаты
            analysis = analyze_results(result, expected_types, not_expected)
            
            # Вывод результатов
            print(f"   📊 Первый результат: {analysis['first_doc_type']}")
            print(f"   📋 Все типы: {', '.join(analysis['doc_types'][:3])}")
            
            # Проверка успешности
            if analysis["found_expected"] and not analysis["found_unexpected"]:
                print(f"   ✅ УСПЕХ - найден нужный тип документа")
                passed_tests += 1
            elif analysis["found_unexpected"]:
                print(f"   ❌ ПРОВАЛ - найден нежелательный тип ({analysis['first_doc_type']})")
            elif not analysis["found_expected"]:
                print(f"   ⚠️  ЧАСТИЧНО - не нашли ожидаемый тип, но и нежелательного нет")
                passed_tests += 0.5
            
            # Показываем первый источник
            sources = result.get("sources", [])
            if sources:
                print(f"   📄 Файл: {sources[0].get('file', 'N/A')}")
            
            print()
    
    # Итоги
    print(f"\n{'='*80}")
    print(f"📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print(f"{'='*80}")
    print(f"✅ Успешных: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
    print(f"❌ Провалов: {total_tests - passed_tests}/{total_tests}")
    
    if passed_tests / total_tests >= 0.8:
        print(f"\n🎉 ОТЛИЧНО! Точность поиска значительно улучшена!")
    elif passed_tests / total_tests >= 0.6:
        print(f"\n✅ ХОРОШО! Поиск стал лучше, но есть что улучшить")
    else:
        print(f"\n⚠️  ТРЕБУЕТСЯ ДОРАБОТКА - точность всё ещё низкая")

if __name__ == "__main__":
    run_tests()

