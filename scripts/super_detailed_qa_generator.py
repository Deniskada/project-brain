#!/usr/bin/env python3
"""
СУПЕР-ДЕТАЛЬНЫЙ генератор QA пар
Генерирует 10+ вопросов для КАЖДОЙ функции/класса/endpoint
Цель: 20,000+ QA пар
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

class SuperDetailedQAGenerator:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.qa_pairs = []
        
    def generate_all(self) -> List[Dict[str, Any]]:
        """Генерация СУПЕР-детальных QA пар"""
        logger.info(f"🚀 СУПЕР-ДЕТАЛЬНАЯ генерация QA для: {self.project_path}")
        
        # 1. 10 вопросов для каждой функции
        func_pairs = self._generate_super_function_qa()
        self.qa_pairs.extend(func_pairs)
        logger.info(f"✅ Функции (детальные): {len(func_pairs)} пар")
        
        # 2. 8 вопросов для каждого класса
        class_pairs = self._generate_super_class_qa()
        self.qa_pairs.extend(class_pairs)
        logger.info(f"✅ Классы (детальные): {len(class_pairs)} пар")
        
        # 3. 12 вопросов для каждого endpoint
        endpoint_pairs = self._generate_super_endpoint_qa()
        self.qa_pairs.extend(endpoint_pairs)
        logger.info(f"✅ Endpoints (детальные): {len(endpoint_pairs)} пар")
        
        # 4. Вопросы про каждое поле модели
        model_pairs = self._generate_model_fields_qa()
        self.qa_pairs.extend(model_pairs)
        logger.info(f"✅ Поля моделей: {len(model_pairs)} пар")
        
        # 5. Вопросы про зависимости
        deps_pairs = self._generate_dependencies_qa()
        self.qa_pairs.extend(deps_pairs)
        logger.info(f"✅ Зависимости: {len(deps_pairs)} пар")
        
        logger.info(f"\n📊 ВСЕГО: {len(self.qa_pairs)} супер-детальных QA пар")
        return self.qa_pairs
    
    def _generate_super_function_qa(self) -> List[Dict[str, Any]]:
        """10 вопросов для КАЖДОЙ функции"""
        pairs = []
        
        for py_file in Path(self.project_path).rglob("*.py"):
            if self._should_skip(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                lines = content.split('\n')
                relative_path = str(py_file.relative_to(self.project_path))
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        func_name = node.name
                        start = node.lineno
                        end = node.end_lineno or start
                        code = '\n'.join(lines[start-1:end])
                        
                        params = [arg.arg for arg in node.args.args]
                        docstring = ast.get_docstring(node) or "Нет описания"
                        is_async = isinstance(node, ast.AsyncFunctionDef)
                        
                        base_answer = f"""📁 Файл: `{relative_path}`
📍 Строки: {start}-{end}

💻 КОД:
```python
{code}
```"""
                        
                        # 10 разных вопросов
                        questions = [
                            (f"Где находится функция {func_name}?", f"{base_answer}\n\n📝 Функция {func_name} находится в файле {relative_path}"),
                            (f"Что делает {func_name}?", f"{base_answer}\n\n📝 {docstring}"),
                            (f"Какие параметры принимает {func_name}?", f"{base_answer}\n\n📝 Параметры: {', '.join(params) if params else 'нет параметров'}"),
                            (f"Как вызвать функцию {func_name}?", f"{base_answer}\n\n📝 Вызов: {'await ' if is_async else ''}{func_name}({', '.join(params)})"),
                            (f"В каком файле функция {func_name}?", f"{base_answer}\n\n📝 Файл: {relative_path}"),
                            (f"На какой строке функция {func_name}?", f"{base_answer}\n\n📝 Строки: {start}-{end}"),
                            (f"Асинхронная ли функция {func_name}?", f"{base_answer}\n\n📝 {'Да, асинхронная' if is_async else 'Нет, синхронная'}"),
                            (f"Код функции {func_name}", f"{base_answer}\n\n📝 Полный код функции выше"),
                            (f"Реализация {func_name}", f"{base_answer}\n\n📝 Реализация функции {func_name}"),
                            (f"Определение функции {func_name}", f"{base_answer}\n\n📝 Определение функции в файле {relative_path}")
                        ]
                        
                        for q, a in questions:
                            pairs.append({"question": q, "answer": a, "metadata": {"file": relative_path, "function": func_name, "lines": f"{start}-{end}"}})
            
            except Exception as e:
                pass
        
        return pairs
    
    def _generate_super_class_qa(self) -> List[Dict[str, Any]]:
        """8 вопросов для КАЖДОГО класса"""
        pairs = []
        
        for py_file in Path(self.project_path).rglob("*.py"):
            if self._should_skip(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                lines = content.split('\n')
                relative_path = str(py_file.relative_to(self.project_path))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_name = node.name
                        start = node.lineno
                        end = node.end_lineno or start
                        code = '\n'.join(lines[start-1:min(end, start+100)])  # Макс 100 строк
                        
                        methods = [c.name for c in node.body if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef))]
                        docstring = ast.get_docstring(node) or "Нет описания"
                        
                        base_answer = f"""📁 Файл: `{relative_path}`
📍 Строки: {start}-{end}

💻 КОД:
```python
{code}
```"""
                        
                        questions = [
                            (f"Где класс {class_name}?", f"{base_answer}\n\n📝 Класс {class_name} в файле {relative_path}"),
                            (f"Что такое {class_name}?", f"{base_answer}\n\n📝 {docstring}"),
                            (f"Методы класса {class_name}", f"{base_answer}\n\n📝 Методы: {', '.join(methods[:10])}"),
                            (f"Код класса {class_name}", f"{base_answer}\n\n📝 Код класса выше"),
                            (f"В каком файле класс {class_name}?", f"{base_answer}\n\n📝 Файл: {relative_path}"),
                            (f"Определение класса {class_name}", f"{base_answer}\n\n📝 Определение в {relative_path}"),
                            (f"Структура класса {class_name}", f"{base_answer}\n\n📝 {len(methods)} методов"),
                            (f"Реализация {class_name}", f"{base_answer}\n\n📝 Реализация класса")
                        ]
                        
                        for q, a in questions:
                            pairs.append({"question": q, "answer": a, "metadata": {"file": relative_path, "class": class_name}})
            
            except Exception as e:
                pass
        
        return pairs
    
    def _generate_super_endpoint_qa(self) -> List[Dict[str, Any]]:
        """12 вопросов для КАЖДОГО endpoint"""
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
                    
                    lines = content.split('\n')
                    relative_path = str(py_file.relative_to(self.project_path))
                    
                    route_pattern = r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']\)'
                    
                    for match in re.finditer(route_pattern, content):
                        method = match.group(1).upper()
                        endpoint = match.group(2)
                        line_num = content[:match.start()].count('\n') + 1
                        
                        code = '\n'.join(lines[line_num-1:line_num+40])
                        
                        role = "unknown"
                        if "/owner/" in relative_path:
                            role = "owner"
                        elif "/manager/" in relative_path:
                            role = "manager"
                        elif "/employee/" in relative_path:
                            role = "employee"
                        
                        full_endpoint = f"/{role}{endpoint if endpoint.startswith('/') else '/' + endpoint}"
                        
                        base_answer = f"""📁 Файл: `{relative_path}`
📍 Строка: {line_num}

💻 ENDPOINT: {method} `{full_endpoint}`

💻 КОД:
```python
{code}
```"""
                        
                        questions = [
                            (f"Endpoint {method} {endpoint}", base_answer),
                            (f"Где endpoint {endpoint}?", f"{base_answer}\n\n📝 В файле {relative_path}"),
                            (f"API {method} {endpoint}", base_answer),
                            (f"Роут {endpoint}", f"{base_answer}\n\n📝 Роль: {role}"),
                            (f"Как работает {endpoint}?", f"{base_answer}\n\n📝 {method} запрос"),
                            (f"Код endpoint {endpoint}", base_answer),
                            (f"Обработчик {endpoint}", f"{base_answer}\n\n📝 Обработчик в {relative_path}"),
                            (f"{method} {full_endpoint}", base_answer),
                            (f"Где {method} {endpoint}?", f"{base_answer}\n\n📝 Строка {line_num}"),
                            (f"Реализация {endpoint}", base_answer),
                            (f"Для роли {role} endpoint {endpoint}", base_answer),
                            (f"API для {endpoint}", f"{base_answer}\n\n📝 {method} метод")
                        ]
                        
                        for q, a in questions:
                            pairs.append({
                                "question": q,
                                "answer": a,
                                "metadata": {
                                    "file": relative_path,
                                    "endpoint": full_endpoint,
                                    "method": method,
                                    "role": role
                                }
                            })
                
                except Exception as e:
                    pass
        
        return pairs
    
    def _generate_model_fields_qa(self) -> List[Dict[str, Any]]:
        """Вопросы про каждое поле каждой модели"""
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
                lines = content.split('\n')
                relative_path = str(py_file.relative_to(self.project_path))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_name = node.name
                        start = node.lineno
                        end = node.end_lineno or start
                        code = '\n'.join(lines[start-1:end])
                        
                        # Ищем поля (Column)
                        fields = []
                        for item in node.body:
                            if isinstance(item, ast.Assign):
                                for target in item.targets:
                                    if isinstance(target, ast.Name):
                                        field_name = target.name
                                        if not field_name.startswith('_'):
                                            fields.append(field_name)
                        
                        base_answer = f"""📁 Файл: `{relative_path}`
📍 Строки: {start}-{end}

💻 МОДЕЛЬ: {class_name}

💻 КОД:
```python
{code[:2000]}
```"""
                        
                        # Вопросы про модель
                        pairs.append({
                            "question": f"Модель {class_name}",
                            "answer": f"{base_answer}\n\n📝 Модель базы данных",
                            "metadata": {"file": relative_path, "model": class_name}
                        })
                        
                        pairs.append({
                            "question": f"Поля модели {class_name}",
                            "answer": f"{base_answer}\n\n📝 Поля: {', '.join(fields[:15])}",
                            "metadata": {"file": relative_path, "model": class_name}
                        })
                        
                        # Вопрос про каждое поле
                        for field in fields[:20]:  # Макс 20 полей
                            pairs.append({
                                "question": f"Поле {field} в модели {class_name}",
                                "answer": f"{base_answer}\n\n📝 Поле {field} является частью модели {class_name}",
                                "metadata": {"file": relative_path, "model": class_name, "field": field}
                            })
            
            except Exception as e:
                pass
        
        return pairs
    
    def _generate_dependencies_qa(self) -> List[Dict[str, Any]]:
        """Вопросы про зависимости и связи"""
        pairs = []
        
        # Карта: что где используется
        usage_map = {}
        
        for py_file in Path(self.project_path).rglob("*.py"):
            if self._should_skip(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                relative_path = str(py_file.relative_to(self.project_path))
                
                # Находим импорты
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                module = alias.name
                                usage_map.setdefault(module, []).append(relative_path)
                        elif isinstance(node, ast.ImportFrom):
                            module = node.module or ""
                            usage_map.setdefault(module, []).append(relative_path)
            
            except Exception as e:
                pass
        
        # Создаем QA про зависимости
        for module, files in usage_map.items():
            if len(files) >= 2:  # Используется минимум в 2 файлах
                pairs.append({
                    "question": f"Где используется {module}?",
                    "answer": f"""📁 Используется в {len(files)} файлах:

{chr(10).join(f'- `{f}`' for f in files[:15])}

📝 Модуль {module} импортируется в {len(files)} местах""",
                    "metadata": {"module": module, "usage_count": len(files)}
                })
                
                pairs.append({
                    "question": f"Зависимость {module}",
                    "answer": f"""📁 Модуль {module} используется в:

{chr(10).join(f'- `{f}`' for f in files[:10])}

📝 Всего использований: {len(files)}""",
                    "metadata": {"module": module}
                })
        
        return pairs
    
    def _should_skip(self, file_path: Path) -> bool:
        skip = ['venv', '__pycache__', 'migrations', 'tests', 'node_modules', '.git', 'htmlcov']
        return any(p in str(file_path) for p in skip)

async def main():
    generator = SuperDetailedQAGenerator("/projects/staffprobot")
    pairs = generator.generate_all()
    
    with open("/tmp/super_detailed_qa_pairs.json", 'w', encoding='utf-8') as f:
        json.dump(pairs, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n✅ Сохранено {len(pairs)} супер-детальных QA пар")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
