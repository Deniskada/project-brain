"""
Индексатор Python файлов
"""
import ast
import os
import logging
from typing import List, Dict, Any, Optional
import re
import fnmatch

logger = logging.getLogger(__name__)

class PythonIndexer:
    def __init__(self):
        self.chunk_size = 1000  # Размер чанка в символах
        self.overlap = 200      # Перекрытие между чанками
    
    def _classify_doc_type(self, file_path: str) -> str:
        """Классификация типа документа по пути"""
        file_path_lower = file_path.lower()
        
        if 'routes' in file_path_lower or 'routers' in file_path_lower:
            return 'route'
        elif 'api' in file_path_lower and 'domain' not in file_path_lower:
            return 'api'
        elif 'models' in file_path_lower or 'entities' in file_path_lower:
            return 'model'
        elif 'services' in file_path_lower:
            return 'service'
        elif 'handlers' in file_path_lower:
            return 'handler'
        elif 'forms' in file_path_lower:
            return 'form'
        elif 'schemas' in file_path_lower:
            return 'schema'
        return 'other'
    
    async def find_files(
        self, 
        project_path: str, 
        include_patterns: List[str],
        exclude_patterns: List[str]
    ) -> List[str]:
        """Поиск Python файлов для индексации"""
        files = []
        
        for root, dirs, filenames in os.walk(project_path):
            # Исключение директорий
            dirs[:] = [d for d in dirs if not any(
                self._matches_pattern(d, exclude_patterns) for exclude in exclude_patterns
            )]
            
            for filename in filenames:
                if filename.endswith('.py'):
                    file_path = os.path.join(root, filename)
                    # Проверка на исключения
                    if not any(self._matches_pattern(file_path, exclude_patterns) for exclude in exclude_patterns):
                        files.append(file_path)
        
        return files
    
    def _matches_pattern(self, path: str, patterns: List[str]) -> bool:
        """Проверка соответствия пути паттерну"""
        for pattern in patterns:
            if pattern.startswith('**/'):
                pattern = pattern[3:]
            if pattern.endswith('/**'):
                pattern = pattern[:-3]
            
            if pattern in path or fnmatch.fnmatch(path, pattern):
                return True
        return False
    
    async def index_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Индексация одного Python файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Парсинг AST
            tree = ast.parse(content)
            
            chunks = []
            
            # Извлечение классов
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    chunk = await self._extract_class_chunk(node, content, file_path)
                    if chunk:
                        chunks.append(chunk)
                
                elif isinstance(node, ast.FunctionDef):
                    chunk = await self._extract_function_chunk(node, content, file_path)
                    if chunk:
                        chunks.append(chunk)
            
            # Извлечение импортов
            imports_chunk = await self._extract_imports_chunk(tree, content, file_path)
            if imports_chunk:
                chunks.append(imports_chunk)
            
            # Извлечение docstring модуля
            module_docstring = ast.get_docstring(tree)
            if module_docstring:
                chunk = {
                    "content": f"Модуль {os.path.basename(file_path)}:\n{module_docstring}",
                    "file": file_path,
                    "lines": "1-10",
                    "start_line": 1,
                    "end_line": 10,
                    "type": "module_docstring",
                    "chunk_id": hash(f"{file_path}_module_docstring")
                }
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Ошибка индексации файла {file_path}: {e}")
            return []
    
    async def _extract_class_chunk(
        self, 
        node: ast.ClassDef, 
        content: str, 
        file_path: str
    ) -> Optional[Dict[str, Any]]:
        """Извлечение информации о классе"""
        try:
            lines = content.split('\n')
            start_line = node.lineno
            end_line = node.end_lineno or start_line
            
            # Получение кода класса
            class_code = '\n'.join(lines[start_line-1:end_line])
            
            # Извлечение docstring
            docstring = ast.get_docstring(node)
            docstring_text = f"\n{docstring}" if docstring else ""
            
            # Извлечение методов
            methods = []
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    methods.append(child.name)
            
            methods_text = f"\nМетоды: {', '.join(methods)}" if methods else ""
            
            chunk_content = f"Класс {node.name}:{docstring_text}{methods_text}\n\nКод:\n{class_code}"
            
            return {
                "content": chunk_content,
                "file": file_path,
                "lines": f"{start_line}-{end_line}",
                "start_line": start_line,
                "end_line": end_line,
                "type": "class",
                "class_name": node.name,
                "chunk_id": hash(f"{file_path}_{node.name}")
            }
            
        except Exception as e:
            logger.error(f"Ошибка извлечения класса {node.name}: {e}")
            return None
    
    async def _extract_function_chunk(
        self, 
        node: ast.FunctionDef, 
        content: str, 
        file_path: str
    ) -> Optional[Dict[str, Any]]:
        """Извлечение информации о функции"""
        try:
            lines = content.split('\n')
            start_line = node.lineno
            end_line = node.end_lineno or start_line
            
            # Получение кода функции
            function_code = '\n'.join(lines[start_line-1:end_line])
            
            # Извлечение docstring
            docstring = ast.get_docstring(node)
            docstring_text = f"\n{docstring}" if docstring else ""
            
            # Извлечение параметров
            params = [arg.arg for arg in node.args.args]
            params_text = f"\nПараметры: {', '.join(params)}" if params else ""
            
            chunk_content = f"Функция {node.name}:{docstring_text}{params_text}\n\nКод:\n{function_code}"
            
            return {
                "content": chunk_content,
                "file": file_path,
                "lines": f"{start_line}-{end_line}",
                "start_line": start_line,
                "end_line": end_line,
                "type": "function",
                "function_name": node.name,
                "chunk_id": hash(f"{file_path}_{node.name}")
            }
            
        except Exception as e:
            logger.error(f"Ошибка извлечения функции {node.name}: {e}")
            return None
    
    async def _extract_imports_chunk(
        self, 
        tree: ast.AST, 
        content: str, 
        file_path: str
    ) -> Optional[Dict[str, Any]]:
        """Извлечение импортов"""
        try:
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"from {module} import {alias.name}")
            
            if not imports:
                return None
            
            imports_text = "\n".join(imports)
            chunk_content = f"Импорты:\n{imports_text}"
            
            return {
                "content": chunk_content,
                "file": file_path,
                "lines": "1-20",
                "start_line": 1,
                "end_line": 20,
                "type": "imports",
                "chunk_id": hash(f"{file_path}_imports")
            }
            
        except Exception as e:
            logger.error(f"Ошибка извлечения импортов: {e}")
            return None
