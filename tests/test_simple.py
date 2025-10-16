#!/usr/bin/env python3
"""
Простой тест API без ChromaDB
"""
import requests
import json

def test_api():
    base_url = "http://localhost:8003"
    
    # Тест 1: Список проектов
    print("Тест 1: Список проектов")
    try:
        response = requests.get(f"{base_url}/api/projects")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Тест 2: Статистика
    print("Тест 2: Статистика")
    try:
        response = requests.get(f"{base_url}/api/stats")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
