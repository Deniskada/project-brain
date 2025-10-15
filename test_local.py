#!/usr/bin/env python3
"""
Локальное тестирование Project Brain без Docker
"""
import sys
import os
import asyncio
import logging

# Добавление пути к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.rag.engine import RAGEngine
from backend.llm.ollama_client import OllamaClient
from backend.storage.chroma_client import ChromaClient

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rag_engine():
    """Тест RAG engine"""
    print("🧪 Тестирование RAG Engine...")
    
    try:
        # Инициализация (без ChromaDB для теста)
        rag = RAGEngine()
        print("✅ RAG Engine создан")
        
        # Тест поиска контекста (заглушка)
        context = await rag.retrieve_context("тестовый запрос", "staffprobot")
        print(f"✅ Поиск контекста: {len(context)} результатов")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка RAG Engine: {e}")
        return False

async def test_ollama_client():
    """Тест Ollama клиента"""
    print("🤖 Тестирование Ollama Client...")
    
    try:
        client = OllamaClient("http://localhost:11434")
        
        # Тест подключения
        if await client.test_connection():
            print("✅ Ollama подключен")
        else:
            print("⚠️  Ollama недоступен (запустите: docker run -d -p 11434:11434 ollama/ollama)")
            return False
        
        # Тест генерации (если Ollama доступен)
        try:
            response = await client.generate_response(
                "Привет! Как дела?",
                [{"content": "Тестовый контекст", "file": "test.py"}],
                max_tokens=100
            )
            print(f"✅ Генерация ответа: {response[:100]}...")
        except Exception as e:
            print(f"⚠️  Ошибка генерации: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка Ollama Client: {e}")
        return False

async def test_chroma_client():
    """Тест ChromaDB клиента"""
    print("🗄️  Тестирование ChromaDB Client...")
    
    try:
        client = ChromaClient("localhost", 8000)
        
        # Попытка инициализации
        try:
            await client.initialize()
            print("✅ ChromaDB подключен")
        except Exception as e:
            print(f"⚠️  ChromaDB недоступен: {e}")
            print("   Запустите: docker run -d -p 8000:8000 chromadb/chroma")
            return False
        
        # Тест сохранения данных
        test_chunks = [
            {
                "content": "Тестовый контент",
                "file": "test.py",
                "lines": "1-10",
                "type": "test",
                "chunk_id": 1
            }
        ]
        
        await client.store_chunks("test_project", test_chunks)
        print("✅ Данные сохранены в ChromaDB")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка ChromaDB Client: {e}")
        return False

async def test_python_indexer():
    """Тест Python индексатора"""
    print("🐍 Тестирование Python Indexer...")
    
    try:
        from backend.indexers.python_indexer import PythonIndexer
        
        indexer = PythonIndexer()
        
        # Тест поиска файлов
        files = await indexer.find_files(
            "/home/sa/projects/staffprobot",
            ["**/*.py"],
            ["**/venv/**", "**/__pycache__/**"]
        )
        
        print(f"✅ Найдено {len(files)} Python файлов")
        
        # Тест индексации одного файла
        if files:
            test_file = files[0]
            chunks = await indexer.index_file(test_file)
            print(f"✅ Проиндексирован файл {test_file}: {len(chunks)} чанков")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка Python Indexer: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🧪 Локальное тестирование Project Brain")
    print("=" * 50)
    
    tests = [
        test_python_indexer,
        test_rag_engine,
        test_ollama_client,
        test_chroma_client
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
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
    else:
        print("❌ Некоторые тесты не прошли")
        print("\n💡 Для полного тестирования запустите:")
        print("   docker compose -f docker-compose.local.yml up -d")

if __name__ == "__main__":
    asyncio.run(main())
