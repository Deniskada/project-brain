#!/usr/bin/env python3
"""
Улучшенный индексатор с большими чанками и полным контекстом
Цель: 85-90% качества ответов
"""
import ast
import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

sys.path.insert(0, '/app')

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class EnhancedPythonIndexer:
    def __init__(self):
        self.min_chunk_size = 500  # Минимум 500 токенов
        self.overlap_size = 100    # Перекрытие 100 токенов
        
    async def index_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Улучшенная индексация файла с полным контекстом"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            chunks = []
            
            # 1. Полный файл как один большой чанк (для общих вопросов)
            full_chunk = await self._create_full_file_chunk(content, file_path)
            if full_chunk:
                chunks.append(full_chunk)
            
            # 2. Классы с полным контекстом
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_chunk = await self._create_enhanced_class_chunk(node, content, file_path)
                    if class_chunk:
                        chunks.append(class_chunk)
            
            # 3. Функции с полным контекстом
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_chunk = await self._create_enhanced_function_chunk(node, content, file_path)
                    if func_chunk:
                        chunks.append(func_chunk)
            
            # 4. Импорты и зависимости
            imports_chunk = await self._create_imports_chunk(tree, content, file_path)
            if imports_chunk:
                chunks.append(imports_chunk)
            
            # 5. Документация модуля
            module_doc_chunk = await self._create_module_doc_chunk(tree, content, file_path)
            if module_doc_chunk:
                chunks.append(module_doc_chunk)
            
            logger.info(f"  📄 {Path(file_path).name}: {len(chunks)} чанков")
            return chunks
            
        except Exception as e:
            logger.error(f"  ❌ Ошибка индексации {file_path}: {e}")
            return []
    
    async def _create_full_file_chunk(self, content: str, file_path: str) -> Optional[Dict[str, Any]]:
        """Создание чанка с полным содержимым файла"""
        if len(content) < 1000:  # Только для небольших файлов
            return {
                "content": f"Полное содержимое файла {Path(file_path).name}:\n\n{content}",
                "file": file_path,
                "lines": f"1-{content.count(chr(10)) + 1}",
                "start_line": 1,
                "end_line": content.count(chr(10)) + 1,
                "type": "full_file",
                "chunk_id": hash(f"{file_path}_full")
            }
        return None
    
    async def _create_enhanced_class_chunk(self, node: ast.ClassDef, content: str, file_path: str) -> Optional[Dict[str, Any]]:
        """Создание улучшенного чанка класса с полным контекстом"""
        try:
            lines = content.split('\n')
            start_line = node.lineno
            end_line = node.end_lineno or start_line
            
            # Получаем код класса
            class_code = '\n'.join(lines[start_line-1:end_line])
            
            # Извлекаем docstring
            docstring = ast.get_docstring(node)
            
            # Извлекаем все методы с их сигнатурами
            methods = []
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_info = {
                        'name': child.name,
                        'line': child.lineno,
                        'is_async': isinstance(child, ast.AsyncFunctionDef),
                        'params': [arg.arg for arg in child.args.args if arg.arg != 'self'],
                        'decorators': [d.id if isinstance(d, ast.Name) else str(d) for d in child.decorator_list]
                    }
                    methods.append(method_info)
            
            # Создаем детальное описание
            methods_text = ""
            for method in methods:
                async_text = "async " if method['is_async'] else ""
                decorators_text = f"@{', @'.join(method['decorators'])} " if method['decorators'] else ""
                params_text = f"({', '.join(method['params'])})" if method['params'] else "()"
                methods_text += f"  - {decorators_text}{async_text}{method['name']}{params_text} (строка {method['line']})\n"
            
            # Формируем контент с полным контекстом
            chunk_content = f"""Класс {node.name} (строки {start_line}-{end_line}):

Описание: {docstring or 'Нет описания'}

Методы класса:
{methods_text}

Полный код класса:
```python
{class_code}
```"""
            
            return {
                "content": chunk_content,
                "file": file_path,
                "lines": f"{start_line}-{end_line}",
                "start_line": start_line,
                "end_line": end_line,
                "type": "class",
                "class_name": node.name,
                "methods_count": len(methods),
                "chunk_id": hash(f"{file_path}_{node.name}")
            }
            
        except Exception as e:
            logger.error(f"Ошибка создания чанка класса {node.name}: {e}")
            return None
    
    async def _create_enhanced_function_chunk(self, node: ast.FunctionDef, content: str, file_path: str) -> Optional[Dict[str, Any]]:
        """Создание улучшенного чанка функции с полным контекстом"""
        try:
            lines = content.split('\n')
            start_line = node.lineno
            end_line = node.end_lineno or start_line
            
            # Получаем код функции
            function_code = '\n'.join(lines[start_line-1:end_line])
            
            # Извлекаем docstring
            docstring = ast.get_docstring(node)
            
            # Извлекаем параметры с типами
            params = []
            param_types = {}
            for arg in node.args.args:
                param_name = arg.arg
                params.append(param_name)
                if arg.annotation:
                    if isinstance(arg.annotation, ast.Name):
                        param_types[param_name] = arg.annotation.id
                    elif isinstance(arg.annotation, ast.Constant):
                        param_types[param_name] = str(arg.annotation.value)
            
            # Извлекаем return type
            return_type = "Any"
            if node.returns:
                if isinstance(node.returns, ast.Name):
                    return_type = node.returns.id
                elif isinstance(node.returns, ast.Constant):
                    return_type = str(node.returns.value)
            
            # Извлекаем декораторы
            decorators = []
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name):
                    decorators.append(decorator.id)
                elif isinstance(decorator, ast.Attribute):
                    decorators.append(decorator.attr)
            
            # Извлекаем вызываемые функции внутри
            called_functions = []
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Name):
                        called_functions.append(child.func.id)
                    elif isinstance(child.func, ast.Attribute):
                        called_functions.append(child.func.attr)
            called_functions = list(set(called_functions))[:15]  # Увеличил до 15
            
            # Формируем детальный контент
            params_text = ", ".join([f"{k}: {v}" for k, v in param_types.items()]) if param_types else ", ".join(params)
            decorators_text = f"@{', @'.join(decorators)} " if decorators else ""
            calls_text = f"Вызывает: {', '.join(called_functions)}" if called_functions else "Не вызывает внешние функции"
            
            chunk_content = f"""Функция {node.name} (строки {start_line}-{end_line}):

Описание: {docstring or 'Нет описания'}

Сигнатура: {decorators_text}def {node.name}({params_text}) -> {return_type}
{calls_text}

Полный код функции:
```python
{function_code}
```"""
            
            return {
                "content": chunk_content,
                "file": file_path,
                "lines": f"{start_line}-{end_line}",
                "start_line": start_line,
                "end_line": end_line,
                "type": "function",
                "function_name": node.name,
                "parameters": params,
                "param_types": param_types,
                "return_type": return_type,
                "decorators": decorators,
                "calls_functions": called_functions,
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "chunk_id": hash(f"{file_path}_{node.name}")
            }
            
        except Exception as e:
            logger.error(f"Ошибка создания чанка функции {node.name}: {e}")
            return None
    
    async def _create_imports_chunk(self, tree: ast.AST, content: str, file_path: str) -> Optional[Dict[str, Any]]:
        """Создание чанка с импортами и зависимостями"""
        try:
            imports = []
            from_imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        from_imports.append(f"from {module} import {alias.name}")
            
            if not imports and not from_imports:
                return None
            
            imports_text = "\n".join(imports) if imports else ""
            from_imports_text = "\n".join(from_imports) if from_imports else ""
            
            chunk_content = f"""Импорты и зависимости модуля {Path(file_path).name}:

Прямые импорты:
{imports_text}

Импорты из модулей:
{from_imports_text}

Всего импортов: {len(imports) + len(from_imports)}"""
            
            return {
                "content": chunk_content,
                "file": file_path,
                "lines": "1-20",
                "start_line": 1,
                "end_line": 20,
                "type": "imports",
                "imports_count": len(imports),
                "from_imports_count": len(from_imports),
                "chunk_id": hash(f"{file_path}_imports")
            }
            
        except Exception as e:
            logger.error(f"Ошибка создания чанка импортов: {e}")
            return None
    
    async def _create_module_doc_chunk(self, tree: ast.AST, content: str, file_path: str) -> Optional[Dict[str, Any]]:
        """Создание чанка с документацией модуля"""
        try:
            module_docstring = ast.get_docstring(tree)
            if not module_docstring or len(module_docstring) < 50:
                return None
            
            chunk_content = f"""Документация модуля {Path(file_path).name}:

{module_docstring}

Этот модуль является частью проекта StaffProBot."""
            
            return {
                "content": chunk_content,
                "file": file_path,
                "lines": "1-10",
                "start_line": 1,
                "end_line": 10,
                "type": "module_docstring",
                "chunk_id": hash(f"{file_path}_module_docstring")
            }
            
        except Exception as e:
            logger.error(f"Ошибка создания чанка документации: {e}")
            return None

async def main():
    """Тестирование улучшенного индексатора"""
    indexer = EnhancedPythonIndexer()
    
    # Тестируем на одном файле
    test_file = "/projects/staffprobot/domain/entities/user.py"
    chunks = await indexer.index_file(test_file)
    
    logger.info(f"\n📊 Результат индексации {test_file}:")
    logger.info(f"Создано чанков: {len(chunks)}")
    
    for i, chunk in enumerate(chunks, 1):
        logger.info(f"\n--- Чанк {i} ---")
        logger.info(f"Тип: {chunk['type']}")
        logger.info(f"Строки: {chunk['lines']}")
        logger.info(f"Размер: {len(chunk['content'])} символов")
        logger.info(f"Превью: {chunk['content'][:200]}...")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
