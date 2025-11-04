#!/usr/bin/env python3
"""
Массовый генератор QA пар (1000+)
Создает QA пары для каждого файла, функции, класса, endpoint
"""
import ast
import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any
import logging
import json

sys.path.insert(0, '/app')

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class MassiveQAGenerator:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.qa_pairs = []
        
    def generate_all_pairs(self) -> List[Dict[str, Any]]:
        """Генерация всех типов QA пар"""
        logger.info(f"🔍 Массовая генерация QA пар для: {self.project_path}")
        
        # 1. QA пары для каждого файла
        file_pairs = self._generate_file_pairs()
        self.qa_pairs.extend(file_pairs)
        logger.info(f"✅ Файлы: {len(file_pairs)} пар")
        
        # 2. QA пары для каждой функции
        function_pairs = self._generate_function_pairs()
        self.qa_pairs.extend(function_pairs)
        logger.info(f"✅ Функции: {len(function_pairs)} пар")
        
        # 3. QA пары для каждого класса
        class_pairs = self._generate_class_pairs()
        self.qa_pairs.extend(class_pairs)
        logger.info(f"✅ Классы: {len(class_pairs)} пар")
        
        # 4. QA пары для каждого API endpoint
        api_pairs = self._generate_api_pairs()
        self.qa_pairs.extend(api_pairs)
        logger.info(f"✅ API endpoints: {len(api_pairs)} пар")
        
        # 5. QA пары для моделей БД
        model_pairs = self._generate_model_pairs()
        self.qa_pairs.extend(model_pairs)
        logger.info(f"✅ Модели БД: {len(model_pairs)} пар")
        
        # 6. QA пары для сервисов
        service_pairs = self._generate_service_pairs()
        self.qa_pairs.extend(service_pairs)
        logger.info(f"✅ Сервисы: {len(service_pairs)} пар")
        
        # 7. QA пары для конфигурации
        config_pairs = self._generate_config_pairs()
        self.qa_pairs.extend(config_pairs)
        logger.info(f"✅ Конфигурация: {len(config_pairs)} пар")
        
        logger.info(f"\n📊 ВСЕГО сгенерировано: {len(self.qa_pairs)} QA пар")
        return self.qa_pairs
    
    def _generate_file_pairs(self) -> List[Dict[str, Any]]:
        """QA пары для каждого файла"""
        pairs = []
        
        for py_file in Path(self.project_path).rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                relative_path = str(py_file.relative_to(self.project_path))
                
                # Определяем тип файла
                file_type = self._get_file_type(relative_path)
                
                # QA пара: "Что делает файл X?"
                question = f"Что делает файл {py_file.stem}?"
                answer = f"""Файл `{relative_path}` является {file_type}.

Размер: {len(content.split(chr(10)))} строк
Содержит: {self._get_file_contents_summary(tree)}

Этот файл является частью проекта StaffProBot."""
                
                pairs.append({
                    "question": question,
                    "answer": answer,
                    "metadata": {
                        "file": relative_path,
                        "category": "file_overview",
                        "difficulty": "easy",
                        "file_type": file_type
                    }
                })
                
                # QA пара: "Где находится файл X?"
                question2 = f"Где находится файл {py_file.stem}?"
                answer2 = f"""Файл {py_file.stem} находится по пути `{relative_path}`.

Это {file_type} в проекте StaffProBot."""
                
                pairs.append({
                    "question": question2,
                    "answer": answer2,
                    "metadata": {
                        "file": relative_path,
                        "category": "file_location",
                        "difficulty": "easy",
                        "file_type": file_type
                    }
                })
                
            except Exception as e:
                logger.error(f"Ошибка обработки файла {py_file}: {e}")
        
        return pairs
    
    def _generate_function_pairs(self) -> List[Dict[str, Any]]:
        """QA пары для каждой функции"""
        pairs = []
        
        for py_file in Path(self.project_path).rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                relative_path = str(py_file.relative_to(self.project_path))
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        docstring = ast.get_docstring(node)
                        if not docstring:
                            continue
                        
                        # QA пара: "Что делает функция X?"
                        question = f"Что делает функция {node.name}?"
                        answer = f"""Функция {node.name} находится в файле `{relative_path}` (строка {node.lineno}).

Описание: {docstring.split('.')[0]}

Сигнатура: {'async ' if isinstance(node, ast.AsyncFunctionDef) else ''}def {node.name}({', '.join([arg.arg for arg in node.args.args])})"""
                        
                        pairs.append({
                            "question": question,
                            "answer": answer,
                            "metadata": {
                                "file": relative_path,
                                "category": "function_description",
                                "difficulty": "medium",
                                "function_name": node.name,
                                "line": node.lineno
                            }
                        })
                        
                        # QA пара: "Как использовать функцию X?"
                        question2 = f"Как использовать функцию {node.name}?"
                        answer2 = f"""Для использования функции {node.name}:

1. Импортируйте её из модуля `{py_file.stem}`
2. Вызовите с правильными параметрами
3. Обработайте возвращаемое значение

Функция находится в файле `{relative_path}` (строка {node.lineno})."""
                        
                        pairs.append({
                            "question": question2,
                            "answer": answer2,
                            "metadata": {
                                "file": relative_path,
                                "category": "function_usage",
                                "difficulty": "medium",
                                "function_name": node.name,
                                "line": node.lineno
                            }
                        })
                
            except Exception as e:
                logger.error(f"Ошибка обработки функций в {py_file}: {e}")
        
        return pairs
    
    def _generate_class_pairs(self) -> List[Dict[str, Any]]:
        """QA пары для каждого класса"""
        pairs = []
        
        for py_file in Path(self.project_path).rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                relative_path = str(py_file.relative_to(self.project_path))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        docstring = ast.get_docstring(node)
                        
                        # Извлекаем методы
                        methods = []
                        for child in node.body:
                            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                methods.append(child.name)
                        
                        # QA пара: "Что делает класс X?"
                        question = f"Что делает класс {node.name}?"
                        answer = f"""Класс {node.name} находится в файле `{relative_path}` (строки {node.lineno}-{node.end_lineno or node.lineno}).

Описание: {docstring or 'Нет описания'}

Методы класса:
{chr(10).join(f"- {method}" for method in methods)}"""
                        
                        pairs.append({
                            "question": question,
                            "answer": answer,
                            "metadata": {
                                "file": relative_path,
                                "category": "class_description",
                                "difficulty": "medium",
                                "class_name": node.name,
                                "line": node.lineno,
                                "methods_count": len(methods)
                            }
                        })
                
            except Exception as e:
                logger.error(f"Ошибка обработки классов в {py_file}: {e}")
        
        return pairs
    
    def _generate_api_pairs(self) -> List[Dict[str, Any]]:
        """QA пары для каждого API endpoint"""
        pairs = []
        
        routes_paths = [
            Path(self.project_path) / "apps" / "web" / "routes",
            Path(self.project_path) / "apps" / "api",
        ]
        
        for routes_path in routes_paths:
            if not routes_path.exists():
                continue
            
            for py_file in routes_path.rglob("*.py"):
                if py_file.name.startswith("_"):
                    continue
                
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    relative_path = str(py_file.relative_to(self.project_path))
                    
                    # Поиск роутов
                    route_pattern = r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']\)'
                    matches = re.finditer(route_pattern, content)
                    
                    for match in matches:
                        method = match.group(1).upper()
                        endpoint = match.group(2)
                        line_num = content[:match.start()].count('\n') + 1
                        
                        # Определяем префикс роли
                        role_prefix = ""
                        if "owner" in str(relative_path):
                            role_prefix = "/owner"
                        elif "manager" in str(relative_path):
                            role_prefix = "/manager"
                        elif "employee" in str(relative_path):
                            role_prefix = "/employee"
                        
                        full_endpoint = f"{role_prefix}{endpoint if endpoint.startswith('/') else '/' + endpoint}"
                        
                        # QA пара: "Какой API endpoint для X?"
                        question = f"Какой API endpoint для {method} операции {endpoint}?"
                        answer = f"""API endpoint для {method} операции {endpoint}:

**{method} `{full_endpoint}`**

Находится в файле: `{relative_path}` (строка {line_num})

Этот endpoint обрабатывает {method.lower()} запросы."""
                        
                        pairs.append({
                            "question": question,
                            "answer": answer,
                            "metadata": {
                                "file": relative_path,
                                "category": "api_endpoint",
                                "difficulty": "easy",
                                "endpoint": full_endpoint,
                                "method": method,
                                "line": line_num
                            }
                        })
                
                except Exception as e:
                    logger.error(f"Ошибка обработки API в {py_file}: {e}")
        
        return pairs
    
    def _generate_model_pairs(self) -> List[Dict[str, Any]]:
        """QA пары для моделей БД"""
        pairs = []
        entities_path = Path(self.project_path) / "domain" / "entities"
        
        if not entities_path.exists():
            return pairs
        
        for py_file in entities_path.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                relative_path = str(py_file.relative_to(self.project_path))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
                        if 'Base' not in bases and 'BaseModel' not in bases:
                            continue
                        
                        model_name = node.name
                        
                        # Извлекаем поля
                        fields = []
                        for item in node.body:
                            if isinstance(item, ast.Assign):
                                for target in item.targets:
                                    if isinstance(target, ast.Name):
                                        field_name = target.name
                                        fields.append(field_name)
                        
                        if fields:
                            # QA пара: "Какие поля в модели X?"
                            question = f"Какие поля есть в модели {model_name}?"
                            answer = f"""Модель {model_name} находится в файле `{relative_path}`.

Основные поля:
{chr(10).join(f"- {field}" for field in fields[:10])}

Это модель базы данных для работы с {model_name.lower()} в системе StaffProBot."""
                            
                            pairs.append({
                                "question": question,
                                "answer": answer,
                                "metadata": {
                                    "file": relative_path,
                                    "category": "database_model",
                                    "difficulty": "easy",
                                    "model_name": model_name,
                                    "fields_count": len(fields)
                                }
                            })
                
            except Exception as e:
                logger.error(f"Ошибка обработки модели {py_file}: {e}")
        
        return pairs
    
    def _generate_service_pairs(self) -> List[Dict[str, Any]]:
        """QA пары для сервисов"""
        pairs = []
        services_path = Path(self.project_path) / "shared" / "services"
        
        if not services_path.exists():
            return pairs
        
        for py_file in services_path.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                relative_path = str(py_file.relative_to(self.project_path))
                
                # QA пара: "Что делает сервис X?"
                question = f"Что делает сервис {py_file.stem}?"
                answer = f"""Сервис {py_file.stem} находится в файле `{relative_path}`.

Это бизнес-логика для работы с {py_file.stem.lower()} в системе StaffProBot.

Содержит функции для обработки данных и бизнес-правил."""
                
                pairs.append({
                    "question": question,
                    "answer": answer,
                    "metadata": {
                        "file": relative_path,
                        "category": "service_description",
                        "difficulty": "medium",
                        "service_name": py_file.stem
                    }
                })
                
            except Exception as e:
                logger.error(f"Ошибка обработки сервиса {py_file}: {e}")
        
        return pairs
    
    def _generate_config_pairs(self) -> List[Dict[str, Any]]:
        """QA пары для конфигурации"""
        pairs = []
        
        config_files = [
            "docker-compose.yml",
            "docker-compose.dev.yml", 
            "docker-compose.prod.yml",
            "requirements.txt",
            "pyproject.toml"
        ]
        
        for config_file in config_files:
            config_path = Path(self.project_path) / config_file
            if config_path.exists():
                # QA пара: "Где находится конфигурация X?"
                question = f"Где находится конфигурация {config_file}?"
                answer = f"""Конфигурация {config_file} находится в корне проекта StaffProBot.

Путь: `{config_file}`

Этот файл содержит настройки для {self._get_config_description(config_file)}."""
                
                pairs.append({
                    "question": question,
                    "answer": answer,
                    "metadata": {
                        "file": config_file,
                        "category": "configuration",
                        "difficulty": "easy",
                        "config_type": config_file.split('.')[-1]
                    }
                })
        
        return pairs
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Проверка, нужно ли пропустить файл"""
        skip_patterns = [
            'venv', '__pycache__', 'migrations', 'tests', 
            'node_modules', '.git', 'htmlcov'
        ]
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _get_file_type(self, file_path: str) -> str:
        """Определение типа файла"""
        if 'routes' in file_path:
            return "файлом роутов API"
        elif 'entities' in file_path:
            return "моделью базы данных"
        elif 'services' in file_path:
            return "сервисом бизнес-логики"
        elif 'handlers' in file_path:
            return "обработчиком команд"
        elif 'config' in file_path:
            return "файлом конфигурации"
        else:
            return "модулем Python"
    
    def _get_file_contents_summary(self, tree: ast.AST) -> str:
        """Краткое описание содержимого файла"""
        functions = []
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
        
        summary_parts = []
        if classes:
            summary_parts.append(f"{len(classes)} классов")
        if functions:
            summary_parts.append(f"{len(functions)} функций")
        
        return ", ".join(summary_parts) if summary_parts else "базовый код"
    
    def _get_config_description(self, config_file: str) -> str:
        """Описание назначения конфигурационного файла"""
        descriptions = {
            'docker-compose.yml': 'основного окружения',
            'docker-compose.dev.yml': 'разработки',
            'docker-compose.prod.yml': 'продакшена',
            'requirements.txt': 'зависимостей Python',
            'pyproject.toml': 'настроек проекта'
        }
        return descriptions.get(config_file, 'конфигурации')

async def main():
    """Тестирование массового генератора"""
    project_path = "/projects/staffprobot"
    
    generator = MassiveQAGenerator(project_path)
    pairs = generator.generate_all_pairs()
    
    # Сохраняем результат
    with open("/tmp/massive_qa_pairs.json", 'w', encoding='utf-8') as f:
        json.dump(pairs, f, ensure_ascii=False, indent=2)
    
    logger.info(f"💾 Сохранено {len(pairs)} QA пар в /tmp/massive_qa_pairs.json")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
