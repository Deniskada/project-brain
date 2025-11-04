#!/usr/bin/env python3
"""
ЦЕЛЕВОЙ генератор QA пар - 10,000+ точных вопросов-ответов
Каждая функция/класс/endpoint получает НЕСКОЛЬКО вопросов с ПОЛНЫМ кодом
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

class TargetedQAGenerator:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.qa_pairs = []
        
    def generate_all(self) -> List[Dict[str, Any]]:
        """Генерация ВСЕХ типов QA пар"""
        logger.info(f"🎯 ЦЕЛЕВАЯ генерация QA пар для: {self.project_path}")
        
        # 1. Для КАЖДОЙ функции - 3 вопроса
        function_pairs = self._generate_function_qa()
        self.qa_pairs.extend(function_pairs)
        logger.info(f"✅ Функции: {len(function_pairs)} пар")
        
        # 2. Для КАЖДОГО класса - 3 вопроса
        class_pairs = self._generate_class_qa()
        self.qa_pairs.extend(class_pairs)
        logger.info(f"✅ Классы: {len(class_pairs)} пар")
        
        # 3. Для КАЖДОГО endpoint - 5 вопросов
        endpoint_pairs = self._generate_endpoint_qa()
        self.qa_pairs.extend(endpoint_pairs)
        logger.info(f"✅ Endpoints: {len(endpoint_pairs)} пар")
        
        # 4. Для КАЖДОГО импорта - 2 вопроса
        import_pairs = self._generate_import_qa()
        self.qa_pairs.extend(import_pairs)
        logger.info(f"✅ Импорты: {len(import_pairs)} пар")
        
        # 5. Для КАЖДОГО файла - 4 вопроса
        file_pairs = self._generate_file_qa()
        self.qa_pairs.extend(file_pairs)
        logger.info(f"✅ Файлы: {len(file_pairs)} пар")
        
        logger.info(f"\n📊 ВСЕГО: {len(self.qa_pairs)} целевых QA пар")
        return self.qa_pairs
    
    def _generate_function_qa(self) -> List[Dict[str, Any]]:
        """3 вопроса для КАЖДОЙ функции"""
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
                        start_line = node.lineno
                        end_line = node.end_lineno or start_line
                        
                        # Получаем полный код функции
                        func_code = '\n'.join(lines[start_line-1:end_line])
                        
                        # Параметры
                        params = [arg.arg for arg in node.args.args]
                        params_str = ', '.join(params)
                        
                        # Docstring
                        docstring = ast.get_docstring(node) or "Нет описания"
                        
                        # Вопрос 1: "Где находится функция X?"
                        q1 = f"Где находится функция {func_name}?"
                        a1 = f"""📁 Файл: `{relative_path}`
📍 Строки: {start_line}-{end_line}

💻 КОД:
```python
{func_code}
```

📝 Объяснение: Функция {func_name} принимает параметры: {params_str}. {docstring[:100]}"""
                        
                        pairs.append({"question": q1, "answer": a1, "metadata": {"file": relative_path, "function": func_name, "lines": f"{start_line}-{end_line}"}})
                        
                        # Вопрос 2: "Что делает функция X?"
                        q2 = f"Что делает функция {func_name}?"
                        a2 = f"""📁 Файл: `{relative_path}`
📍 Строки: {start_line}-{end_line}

💻 КОД:
```python
{func_code}
```

📝 Объяснение: {docstring}"""
                        
                        pairs.append({"question": q2, "answer": a2, "metadata": {"file": relative_path, "function": func_name}})
                        
                        # Вопрос 3: "Как использовать функцию X?"
                        q3 = f"Как использовать функцию {func_name}?"
                        a3 = f"""📁 Файл: `{relative_path}`
📍 Строки: {start_line}-{end_line}

💻 ПРИМЕР:
```python
from {relative_path.replace('/', '.').replace('.py', '')} import {func_name}

result = {'await ' if isinstance(node, ast.AsyncFunctionDef) else ''}{func_name}({params_str})
```

💻 ПОЛНЫЙ КОД ФУНКЦИИ:
```python
{func_code}
```"""
                        
                        pairs.append({"question": q3, "answer": a3, "metadata": {"file": relative_path, "function": func_name}})
                
            except Exception as e:
                logger.error(f"Ошибка обработки {py_file}: {e}")
        
        return pairs
    
    def _generate_class_qa(self) -> List[Dict[str, Any]]:
        """3 вопроса для КАЖДОГО класса"""
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
                        start_line = node.lineno
                        end_line = node.end_lineno or start_line
                        
                        # Полный код класса
                        class_code = '\n'.join(lines[start_line-1:end_line])
                        
                        # Методы
                        methods = []
                        for child in node.body:
                            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                methods.append(child.name)
                        
                        methods_str = ', '.join(methods[:10])
                        docstring = ast.get_docstring(node) or "Нет описания"
                        
                        # Вопрос 1: "Где находится класс X?"
                        q1 = f"Где находится класс {class_name}?"
                        a1 = f"""📁 Файл: `{relative_path}`
📍 Строки: {start_line}-{end_line}

💻 КОД:
```python
{class_code[:1000]}{'...' if len(class_code) > 1000 else ''}
```

📝 Объяснение: Класс {class_name} содержит методы: {methods_str}"""
                        
                        pairs.append({"question": q1, "answer": a1, "metadata": {"file": relative_path, "class": class_name}})
                        
                        # Вопрос 2: "Какие методы есть в классе X?"
                        q2 = f"Какие методы есть в классе {class_name}?"
                        a2 = f"""📁 Файл: `{relative_path}`
📍 Строки: {start_line}-{end_line}

💻 МЕТОДЫ:
{chr(10).join(f'- {m}' for m in methods)}

💻 КОД КЛАССА:
```python
{class_code[:1000]}{'...' if len(class_code) > 1000 else ''}
```"""
                        
                        pairs.append({"question": q2, "answer": a2, "metadata": {"file": relative_path, "class": class_name}})
                        
                        # Вопрос 3: "Что делает класс X?"
                        q3 = f"Что делает класс {class_name}?"
                        a3 = f"""📁 Файл: `{relative_path}`
📍 Строки: {start_line}-{end_line}

💻 КОД:
```python
{class_code[:1000]}{'...' if len(class_code) > 1000 else ''}
```

📝 Объяснение: {docstring}"""
                        
                        pairs.append({"question": q3, "answer": a3, "metadata": {"file": relative_path, "class": class_name}})
                
            except Exception as e:
                logger.error(f"Ошибка обработки класса {py_file}: {e}")
        
        return pairs
    
    def _generate_endpoint_qa(self) -> List[Dict[str, Any]]:
        """5 вопросов для КАЖДОГО endpoint"""
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
                    
                    # Находим все роуты
                    route_pattern = r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']\)'
                    
                    for match in re.finditer(route_pattern, content):
                        method = match.group(1).upper()
                        endpoint = match.group(2)
                        line_num = content[:match.start()].count('\n') + 1
                        
                        # Находим функцию-обработчик (следующая def после @router)
                        func_pattern = r'@router\.' + match.group(1) + r'[^\n]+\n(?:async )?def ([^\(]+)\('
                        func_match = re.search(func_pattern, content[match.start():])
                        func_name = func_match.group(1) if func_match else "unknown"
                        
                        # Получаем код функции (30 строк после роута)
                        func_code = '\n'.join(lines[line_num-1:line_num+30])
                        
                        # Определяем роль
                        role = "unknown"
                        if "/owner/" in relative_path or "/owner" in endpoint:
                            role = "owner"
                        elif "/manager/" in relative_path or "/manager" in endpoint:
                            role = "manager"
                        elif "/employee/" in relative_path or "/employee" in endpoint:
                            role = "employee"
                        
                        full_endpoint = f"/{role}{endpoint if endpoint.startswith('/') else '/' + endpoint}"
                        
                        # 5 разных вопросов для каждого endpoint
                        questions = [
                            (f"Какой API endpoint для {method} {endpoint}?", f"API endpoint: {method} `{full_endpoint}`"),
                            (f"Где находится роут {method} {endpoint}?", f"Роут находится в файле `{relative_path}`"),
                            (f"Как работает endpoint {endpoint}?", f"Endpoint обрабатывается функцией {func_name}"),
                            (f"Что возвращает endpoint {full_endpoint}?", f"Endpoint {full_endpoint} обрабатывает {method} запросы"),
                            (f"Какие параметры принимает {endpoint}?", f"Параметры определены в функции {func_name}")
                        ]
                        
                        for q, summary in questions:
                            answer = f"""📁 Файл: `{relative_path}`
📍 Строка: {line_num}

💻 ENDPOINT: {method} `{full_endpoint}`

💻 КОД:
```python
{func_code}
```

📝 Объяснение: {summary}. Роль: {role}"""
                            
                            pairs.append({
                                "question": q,
                                "answer": answer,
                                "metadata": {
                                    "file": relative_path,
                                    "endpoint": full_endpoint,
                                    "method": method,
                                    "role": role,
                                    "line": line_num
                                }
                            })
                
                except Exception as e:
                    logger.error(f"Ошибка обработки endpoint {py_file}: {e}")
        
        return pairs
    
    def _generate_import_qa(self) -> List[Dict[str, Any]]:
        """2 вопроса для каждого импорта"""
        pairs = []
        imports_map = {}  # модуль -> список файлов
        
        for py_file in Path(self.project_path).rglob("*.py"):
            if self._should_skip(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                relative_path = str(py_file.relative_to(self.project_path))
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                module = alias.name
                                imports_map.setdefault(module, []).append(relative_path)
                        elif isinstance(node, ast.ImportFrom):
                            module = node.module or ""
                            for alias in node.names:
                                full_name = f"{module}.{alias.name}" if module else alias.name
                                imports_map.setdefault(full_name, []).append(relative_path)
            
            except Exception as e:
                pass
        
        # Создаем QA для популярных импортов
        for module, files in imports_map.items():
            if len(files) > 1:  # Только если используется в нескольких местах
                # Вопрос 1: "Где импортируется X?"
                q1 = f"Где импортируется {module}?"
                a1 = f"""📁 Импортируется в {len(files)} файлах:

{chr(10).join(f'- `{f}`' for f in files[:10])}

📝 Объяснение: Модуль {module} используется в {len(files)} местах проекта"""
                
                pairs.append({"question": q1, "answer": a1, "metadata": {"import": module}})
                
                # Вопрос 2: "Как используется X?"
                q2 = f"Как используется {module}?"
                a2 = f"""📁 Используется в файлах:
{chr(10).join(f'- `{f}`' for f in files[:5])}

📝 Объяснение: Модуль {module} импортируется для использования в различных частях приложения"""
                
                pairs.append({"question": q2, "answer": a2, "metadata": {"import": module}})
        
        return pairs
    
    def _generate_file_qa(self) -> List[Dict[str, Any]]:
        """4 вопроса для КАЖДОГО файла"""
        pairs = []
        
        for py_file in Path(self.project_path).rglob("*.py"):
            if self._should_skip(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                relative_path = str(py_file.relative_to(self.project_path))
                file_name = py_file.stem
                
                # Подсчет функций/классов
                functions = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
                
                # 4 вопроса
                q1 = f"Что делает файл {file_name}?"
                a1 = f"""📁 Файл: `{relative_path}`
📍 Строк: {len(content.split(chr(10)))}

💻 СОДЕРЖИМОЕ:
- Функций: {len(functions)}
- Классов: {len(classes)}

📝 Первые строки:
```python
{chr(10).join(content.split(chr(10))[:20])}
```"""
                
                pairs.append({"question": q1, "answer": a1, "metadata": {"file": relative_path}})
                
                q2 = f"Где находится файл {file_name}?"
                a2 = f"""📁 Файл: `{relative_path}`

📝 Объяснение: Файл {file_name}.py находится по пути {relative_path} в проекте StaffProBot"""
                
                pairs.append({"question": q2, "answer": a2, "metadata": {"file": relative_path}})
                
                q3 = f"Какие функции есть в файле {file_name}?"
                a3 = f"""📁 Файл: `{relative_path}`

💻 ФУНКЦИИ:
{chr(10).join(f'- {f}' for f in functions[:20])}

Всего функций: {len(functions)}"""
                
                pairs.append({"question": q3, "answer": a3, "metadata": {"file": relative_path}})
                
                q4 = f"Какие классы есть в файле {file_name}?"
                a4 = f"""📁 Файл: `{relative_path}`

💻 КЛАССЫ:
{chr(10).join(f'- {c}' for c in classes)}

Всего классов: {len(classes)}"""
                
                pairs.append({"question": q4, "answer": a4, "metadata": {"file": relative_path}})
            
            except Exception as e:
                pass
        
        return pairs
    
    def _should_skip(self, file_path: Path) -> bool:
        """Проверка, пропускать ли файл"""
        skip_patterns = ['venv', '__pycache__', 'migrations', 'tests', 'node_modules', '.git', 'htmlcov']
        return any(p in str(file_path) for p in skip_patterns)

async def main():
    """Генерация ВСЕХ целевых QA пар"""
    generator = TargetedQAGenerator("/projects/staffprobot")
    pairs = generator.generate_all()
    
    # Сохраняем
    with open("/tmp/targeted_qa_pairs.json", 'w', encoding='utf-8') as f:
        json.dump(pairs, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n✅ Сохранено {len(pairs)} целевых QA пар в /tmp/targeted_qa_pairs.json")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
