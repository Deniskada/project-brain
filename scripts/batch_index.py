#!/usr/bin/env python3
"""
Скрипт для пакетной индексации проекта
Запускает индексацию итерациями по 20 файлов с проверкой статуса
"""
import requests
import time
import sys

API_URL = "http://localhost:8003/api"
PROJECT = "staffprobot"
BATCH_ITERATIONS = 20  # Количество итераций
WAIT_TIME = 60  # Секунд между итерациями

def get_status():
    """Получение текущего статуса индексации"""
    try:
        response = requests.get(f"{API_URL}/index/status/{PROJECT}")
        if response.status_code == 200:
            data = response.json()
            return data.get("total_documents", 0)
        return 0
    except Exception as e:
        print(f"Ошибка получения статуса: {e}")
        return 0

def trigger_indexing():
    """Запуск индексации"""
    try:
        response = requests.post(f"{API_URL}/index/{PROJECT}", timeout=5)
        if response.status_code == 200:
            print("✅ Индексация запущена")
            return True
        else:
            print(f"❌ Ошибка: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️  Запрос отправлен (фоновая задача): {e}")
        return True  # Это нормально для фоновой задачи

def main():
    print("=" * 60)
    print(f"🚀 Пакетная индексация проекта: {PROJECT}")
    print(f"📦 Батч: 30 файлов за итерацию")
    print(f"⏱️  Задержка между итерациями: {WAIT_TIME} секунд")
    print("=" * 60)
    print()
    
    initial_docs = get_status()
    print(f"📊 Начальное состояние: {initial_docs} документов в базе")
    print(f"💡 Каждая итерация добавляет ~30 файлов, начинаем с файла #{initial_docs + 1}")
    print()
    
    prev_docs = initial_docs
    
    for iteration in range(1, BATCH_ITERATIONS + 1):
        print(f"\n{'=' * 60}")
        print(f"📍 Итерация {iteration}/{BATCH_ITERATIONS} (файлы с #{prev_docs + 1})")
        print(f"{'=' * 60}")
        
        # Запуск индексации
        print(f"[{time.strftime('%H:%M:%S')}] Запуск индексации...")
        trigger_indexing()
        
        # Ждем завершения (сократим до 3 минут)
        print(f"⏳ Ожидание {WAIT_TIME} секунд...")
        for i in range(WAIT_TIME // 10):
            time.sleep(10)
            current = get_status()
            if current > prev_docs:
                print(f"  └─ {current} документов (+{current - prev_docs})")
        
        # Проверка финального статуса
        current_docs = get_status()
        added_this_iteration = current_docs - prev_docs
        total_added = current_docs - initial_docs
        
        print(f"📊 Итерация завершена: {current_docs} документов")
        print(f"   └─ Добавлено в этой итерации: {added_this_iteration}")
        print(f"   └─ Всего добавлено: {total_added}")
        
        # Если ничего не добавилось - индексация завершена
        if added_this_iteration == 0:
            print("\n✅ Индексация завершена! Новых файлов нет.")
            break
        
        prev_docs = current_docs
    
    print("\n" + "=" * 60)
    print("✅ Пакетная индексация завершена!")
    final_docs = get_status()
    total_added = final_docs - initial_docs
    print(f"📊 Финальный результат: {final_docs} документов (добавлено: {total_added})")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⛔ Прервано пользователем")
        sys.exit(0)

