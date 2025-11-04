#!/usr/bin/env python3
"""
Автоматический генератор обучающих пар вопрос-ответ из кодовой базы
Извлекает структуры, паттерны и документацию для создания QA пар
"""
import ast
import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QAPairGenerator:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.qa_pairs = []
        
    def generate_all_pairs(self) -> List[Dict[str, Any]]:
        """Генерация всех типов QA пар"""
        logger.info(f"🔍 Сканирование проекта: {self.project_path}")
        
        # 1. QA пары из моделей БД
        model_pairs = self._generate_model_pairs()
        self.qa_pairs.extend(model_pairs)
        logger.info(f"✅ Создано {len(model_pairs)} пар из моделей")
        
        # 2. QA пары из API роутов
        route_pairs = self._generate_route_pairs()
        self.qa_pairs.extend(route_pairs)
        logger.info(f"✅ Создано {len(route_pairs)} пар из роутов")
        
        # 3. QA пары из функций с docstrings
        function_pairs = self._generate_function_pairs()
        self.qa_pairs.extend(function_pairs)
        logger.info(f"✅ Создано {len(function_pairs)} пар из функций")
        
        # 4. QA пары из TODO/FIXME комментариев
        issue_pairs = self._generate_issue_pairs()
        self.qa_pairs.extend(issue_pairs)
        logger.info(f"✅ Создано {len(issue_pairs)} пар из комментариев")
        
        logger.info(f"\n📊 Всего сгенерировано: {len(self.qa_pairs)} QA пар")
        return self.qa_pairs
    
    def _generate_model_pairs(self) -> List[Dict[str, Any]]:
        """Генерация QA пар из моделей БД"""
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
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Пропускаем не-модели
                        bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
                        if 'Base' not in bases and 'BaseModel' not in bases:
                            continue
                        
                        model_name = node.name
                        start_line = node.lineno
                        end_line = node.end_lineno or start_line
                        relative_path = py_file.relative_to(self.project_path)
                        
                        # Извлечение полей
                        fields = []
                        for item in node.body:
                            if isinstance(item, ast.Assign):
                                for target in item.targets:
                                    if isinstance(target, ast.Name):
                                        field_name = target.name
                                        # Попытка определить тип
                                        field_type = "Any"
                                        if isinstance(item.value, ast.Call):
                                            if hasattr(item.value.func, 'id'):
                                                field_type = item.value.func.id
                                        fields.append(f"{field_name} ({field_type})")
                        
                        if fields:
                            question = f"Какие поля есть в модели {model_name}?"
                            answer = f"""Модель {model_name} находится в файле {relative_path} (строки {start_line}-{end_line}).

Основные поля:
{chr(10).join('- ' + f for f in fields[:10])}

Это модель базы данных для работы с {model_name.lower()} в системе."""

                            pairs.append({
                                "question": question,
                                "answer": answer,
                                "metadata": {
                                    "file": str(relative_path),
                                    "category": "database",
                                    "difficulty": "easy",
                                    "model_name": model_name
                                }
                            })
                            
                            # Дополнительный вопрос "Где находится модель X?"
                            question2 = f"Где находится модель {model_name} в проекте?"
                            answer2 = f"""Модель {model_name} находится в файле **{relative_path}** (строки {start_line}-{end_line}).

Путь: `{relative_path}`

Это модель базы данных, которая определяет структуру таблицы для {model_name.lower()}."""

                            pairs.append({
                                "question": question2,
                                "answer": answer2,
                                "metadata": {
                                    "file": str(relative_path),
                                    "category": "architecture",
                                    "difficulty": "easy",
                                    "model_name": model_name
                                }
                            })
                
            except Exception as e:
                logger.error(f"Ошибка обработки {py_file}: {e}")
        
        return pairs
    
    def _generate_route_pairs(self) -> List[Dict[str, Any]]:
        """Генерация QA пар из API роутов"""
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
                    
                    # Поиск декораторов @router.get, @router.post и т.д.
                    route_pattern = r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']\)'
                    matches = re.finditer(route_pattern, content)
                    
                    relative_path = py_file.relative_to(self.project_path)
                    
                    for match in matches:
                        method = match.group(1).upper()
                        endpoint = match.group(2)
                        line_num = content[:match.start()].count('\n') + 1
                        
                        # Определяем префикс роли из пути
                        role_prefix = ""
                        if "owner" in str(relative_path):
                            role_prefix = "/owner"
                        elif "manager" in str(relative_path):
                            role_prefix = "/manager"
                        elif "employee" in str(relative_path):
                            role_prefix = "/employee"
                        
                        full_endpoint = f"{role_prefix}{endpoint if endpoint.startswith('/') else '/' + endpoint}"
                        
                        # Определяем сущность из пути файла
                        entity = py_file.stem
                        if entity == "__init__":
                            entity = py_file.parent.name
                        
                        question = f"Какой API endpoint для {method} операции с {entity}?"
                        answer = f"""API endpoint для {method} операции с {entity}:

**{method} `{full_endpoint}`**

Находится в файле: `{relative_path}` (строка ~{line_num})

Этот endpoint обрабатывает {method.lower()} запросы для работы с {entity}."""

                        pairs.append({
                            "question": question,
                            "answer": answer,
                            "metadata": {
                                "file": str(relative_path),
                                "category": "api",
                                "difficulty": "medium",
                                "endpoint": full_endpoint,
                                "method": method
                            }
                        })
                
                except Exception as e:
                    logger.error(f"Ошибка обработки роутов {py_file}: {e}")
        
        return pairs
    
    def _generate_function_pairs(self) -> List[Dict[str, Any]]:
        """Генерация QA пар из функций с docstrings"""
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
                
                relative_path = py_file.relative_to(self.project_path)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                        docstring = ast.get_docstring(node)
                        if not docstring or len(docstring) < 20:
                            continue
                        
                        func_name = node.name
                        start_line = node.lineno
                        end_line = node.end_lineno or start_line
                        
                        # Извлечение параметров
                        params = []
                        for arg in node.args.args:
                            if arg.arg != 'self':
                                params.append(arg.arg)
                        
                        question = f"Что делает функция {func_name} в {py_file.stem}?"
                        answer = f"""Функция **{func_name}** находится в файле `{relative_path}` (строки {start_line}-{end_line}).

**Описание:** {docstring.split('.')[0]}.

**Параметры:** {', '.join(params) if params else 'нет параметров'}

Это сервисная функция для бизнес-логики приложения."""

                        pairs.append({
                            "question": question,
                            "answer": answer,
                            "metadata": {
                                "file": str(relative_path),
                                "category": "business_logic",
                                "difficulty": "medium",
                                "function_name": func_name
                            }
                        })
            
            except Exception as e:
                logger.error(f"Ошибка обработки функций {py_file}: {e}")
        
        return pairs
    
    def _generate_issue_pairs(self) -> List[Dict[str, Any]]:
        """Генерация QA пар из TODO/FIXME комментариев"""
        pairs = []
        todo_pattern = r'#\s*(TODO|FIXME|NOTE|HACK|XXX):?\s*(.+)'
        
        for py_file in Path(self.project_path).rglob("*.py"):
            if any(x in str(py_file) for x in ['venv', '__pycache__', 'migrations', 'tests']):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                relative_path = py_file.relative_to(self.project_path)
                
                for match in re.finditer(todo_pattern, content):
                    marker = match.group(1)
                    comment = match.group(2).strip()
                    line_num = content[:match.start()].count('\n') + 1
                    
                    if marker == "TODO":
                        question = f"Какие планируемые улучшения есть в {py_file.stem}?"
                    elif marker == "FIXME":
                        question = f"Какие известные проблемы есть в {py_file.stem}?"
                    else:
                        question = f"Какие особенности реализации в {py_file.stem}?"
                    
                    answer = f"""В файле `{relative_path}` (строка {line_num}) есть пометка:

**{marker}:** {comment}

Это {
    'планируемое улучшение' if marker == 'TODO' else
    'известная проблема, требующая исправления' if marker == 'FIXME' else
    'важная заметка для разработчиков'
}."""

                    pairs.append({
                        "question": question,
                        "answer": answer,
                        "metadata": {
                            "file": str(relative_path),
                            "category": "troubleshooting",
                            "difficulty": "medium",
                            "issue_type": marker
                        }
                    })
            
            except Exception as e:
                logger.error(f"Ошибка поиска комментариев {py_file}: {e}")
        
        return pairs[:10]  # Ограничиваем до 10 самых важных
    
    def save_pairs(self, output_file: str = "generated_qa_pairs.json"):
        """Сохранение сгенерированных пар в JSON"""
        import json
        
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.qa_pairs, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Пары сохранены в {output_path}")

def main():
    project_path = sys.argv[1] if len(sys.argv) > 1 else "/projects/staffprobot"
    
    generator = QAPairGenerator(project_path)
    pairs = generator.generate_all_pairs()
    
    # Сохранение
    generator.save_pairs("/tmp/generated_qa_pairs.json")
    
    # Вывод примеров
    logger.info("\n📝 Примеры сгенерированных пар:\n")
    for i, pair in enumerate(pairs[:3], 1):
        logger.info(f"--- Пример {i} ---")
        logger.info(f"Q: {pair['question']}")
        logger.info(f"A: {pair['answer'][:200]}...")
        logger.info(f"Категория: {pair['metadata']['category']}\n")

if __name__ == "__main__":
    main()

