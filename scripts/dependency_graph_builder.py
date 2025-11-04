#!/usr/bin/env python3
"""
Генератор графа связей между файлами проекта
Создает cross-references для лучшего поиска
"""
import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Any
import logging
import json

sys.path.insert(0, '/app')

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class DependencyGraphBuilder:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.graph = {
            'files': {},      # file_path -> {imports, exports, functions, classes}
            'functions': {},  # function_name -> {file, line, called_by, calls}
            'classes': {},    # class_name -> {file, line, methods, used_by}
            'imports': {}     # module_name -> {imported_by, exports}
        }
        
    def build_graph(self) -> Dict[str, Any]:
        """Построение полного графа зависимостей"""
        logger.info(f"🔍 Сканирование проекта: {self.project_path}")
        
        # Сканируем все Python файлы
        python_files = list(Path(self.project_path).rglob("*.py"))
        logger.info(f"📄 Найдено Python файлов: {len(python_files)}")
        
        for py_file in python_files:
            if self._should_skip_file(py_file):
                continue
                
            try:
                self._analyze_file(py_file)
            except Exception as e:
                logger.error(f"❌ Ошибка анализа {py_file}: {e}")
        
        logger.info(f"📊 Граф построен:")
        logger.info(f"  • Файлов: {len(self.graph['files'])}")
        logger.info(f"  • Функций: {len(self.graph['functions'])}")
        logger.info(f"  • Классов: {len(self.graph['classes'])}")
        logger.info(f"  • Импортов: {len(self.graph['imports'])}")
        
        return self.graph
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Проверка, нужно ли пропустить файл"""
        skip_patterns = [
            'venv', '__pycache__', 'migrations', 'tests', 
            'node_modules', '.git', 'htmlcov'
        ]
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _analyze_file(self, file_path: Path):
        """Анализ одного файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            relative_path = str(file_path.relative_to(self.project_path))
            
            file_info = {
                'path': relative_path,
                'imports': [],
                'exports': [],
                'functions': [],
                'classes': [],
                'lines_count': len(content.split('\n'))
            }
            
            # Анализ импортов
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        import_name = alias.name
                        file_info['imports'].append(import_name)
                        self._add_import_usage(import_name, relative_path)
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        import_name = f"{module}.{alias.name}" if module else alias.name
                        file_info['imports'].append(import_name)
                        self._add_import_usage(import_name, relative_path)
            
            # Анализ функций
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_info = self._analyze_function(node, relative_path, content)
                    file_info['functions'].append(func_info['name'])
                    self.graph['functions'][func_info['name']] = func_info
            
            # Анализ классов
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = self._analyze_class(node, relative_path, content)
                    file_info['classes'].append(class_info['name'])
                    self.graph['classes'][class_info['name']] = class_info
            
            self.graph['files'][relative_path] = file_info
            
        except Exception as e:
            logger.error(f"Ошибка анализа файла {file_path}: {e}")
    
    def _analyze_function(self, node: ast.FunctionDef, file_path: str, content: str) -> Dict[str, Any]:
        """Анализ функции"""
        lines = content.split('\n')
        start_line = node.lineno
        end_line = node.end_lineno or start_line
        
        # Извлекаем вызываемые функции
        called_functions = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    called_functions.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    called_functions.append(child.func.attr)
        
        return {
            'name': node.name,
            'file': file_path,
            'line': start_line,
            'end_line': end_line,
            'is_async': isinstance(node, ast.AsyncFunctionDef),
            'called_by': [],  # Заполнится позже
            'calls': list(set(called_functions)),
            'parameters': [arg.arg for arg in node.args.args],
            'docstring': ast.get_docstring(node)
        }
    
    def _analyze_class(self, node: ast.ClassDef, file_path: str, content: str) -> Dict[str, Any]:
        """Анализ класса"""
        lines = content.split('\n')
        start_line = node.lineno
        end_line = node.end_lineno or start_line
        
        # Извлекаем методы
        methods = []
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append({
                    'name': child.name,
                    'line': child.lineno,
                    'is_async': isinstance(child, ast.AsyncFunctionDef)
                })
        
        return {
            'name': node.name,
            'file': file_path,
            'line': start_line,
            'end_line': end_line,
            'methods': methods,
            'used_by': [],  # Заполнится позже
            'docstring': ast.get_docstring(node)
        }
    
    def _add_import_usage(self, import_name: str, file_path: str):
        """Добавление информации об использовании импорта"""
        if import_name not in self.graph['imports']:
            self.graph['imports'][import_name] = {
                'imported_by': [],
                'exports': []
            }
        
        if file_path not in self.graph['imports'][import_name]['imported_by']:
            self.graph['imports'][import_name]['imported_by'].append(file_path)
    
    def build_cross_references(self):
        """Построение cross-references между функциями и классами"""
        logger.info("🔗 Построение cross-references...")
        
        # Находим кто вызывает какие функции
        for func_name, func_info in self.graph['functions'].items():
            for called_func in func_info['calls']:
                if called_func in self.graph['functions']:
                    if func_name not in self.graph['functions'][called_func]['called_by']:
                        self.graph['functions'][called_func]['called_by'].append(func_name)
        
        # Находим где используются классы
        for class_name, class_info in self.graph['classes'].items():
            for file_path, file_info in self.graph['files'].items():
                if class_name in file_info['imports']:
                    if file_path not in class_info['used_by']:
                        class_info['used_by'].append(file_path)
        
        logger.info("✅ Cross-references построены")
    
    def generate_enhanced_qa_pairs(self) -> List[Dict[str, Any]]:
        """Генерация улучшенных QA пар на основе графа"""
        qa_pairs = []
        
        # QA пары для функций
        for func_name, func_info in self.graph['functions'].items():
            if len(func_info['called_by']) > 0:  # Только используемые функции
                question = f"Где используется функция {func_name}?"
                answer = f"""Функция {func_name} находится в файле `{func_info['file']}` (строка {func_info['line']}).

Используется в следующих местах:
{chr(10).join(f"- {caller}" for caller in func_info['called_by'])}

Сигнатура: {'async ' if func_info['is_async'] else ''}def {func_name}({', '.join(func_info['parameters'])})"""
                
                qa_pairs.append({
                    "question": question,
                    "answer": answer,
                    "metadata": {
                        "category": "function_usage",
                        "difficulty": "medium",
                        "function_name": func_name
                    }
                })
        
        # QA пары для классов
        for class_name, class_info in self.graph['classes'].items():
            if len(class_info['used_by']) > 0:  # Только используемые классы
                question = f"Где используется класс {class_name}?"
                answer = f"""Класс {class_name} находится в файле `{class_info['file']}` (строки {class_info['line']}-{class_info['end_line']}).

Используется в файлах:
{chr(10).join(f"- {file}" for file in class_info['used_by'])}

Методы класса:
{chr(10).join(f"- {method['name']} (строка {method['line']})" for method in class_info['methods'])}"""
                
                qa_pairs.append({
                    "question": question,
                    "answer": answer,
                    "metadata": {
                        "category": "class_usage",
                        "difficulty": "medium",
                        "class_name": class_name
                    }
                })
        
        # QA пары для импортов
        for import_name, import_info in self.graph['imports'].items():
            if len(import_info['imported_by']) > 1:  # Используется в нескольких местах
                question = f"Где импортируется {import_name}?"
                answer = f"""Модуль {import_name} импортируется в следующих файлах:

{chr(10).join(f"- {file}" for file in import_info['imported_by'])}

Всего используется в {len(import_info['imported_by'])} файлах."""
                
                qa_pairs.append({
                    "question": question,
                    "answer": answer,
                    "metadata": {
                        "category": "import_usage",
                        "difficulty": "easy",
                        "import_name": import_name
                    }
                })
        
        logger.info(f"📝 Сгенерировано {len(qa_pairs)} QA пар на основе графа")
        return qa_pairs
    
    def save_graph(self, output_file: str = "/tmp/dependency_graph.json"):
        """Сохранение графа в файл"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.graph, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Граф сохранен в {output_file}")

async def main():
    """Тестирование построения графа"""
    project_path = "/projects/staffprobot"
    
    builder = DependencyGraphBuilder(project_path)
    graph = builder.build_graph()
    builder.build_cross_references()
    
    # Генерируем QA пары
    qa_pairs = builder.generate_enhanced_qa_pairs()
    
    # Сохраняем результаты
    builder.save_graph()
    
    with open("/tmp/graph_qa_pairs.json", 'w', encoding='utf-8') as f:
        json.dump(qa_pairs, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ Готово! Создано {len(qa_pairs)} QA пар на основе графа")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
