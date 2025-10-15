"""
Анализатор структуры проекта
Сканирует роуты, модели БД, зависимости
"""
import os
import ast
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import re

logger = logging.getLogger(__name__)

class ProjectStructureAnalyzer:
    """Анализ структуры проекта"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.routes = []
        self.models = []
        self.services = []
        self.dependencies = {}
    
    async def analyze(self) -> Dict[str, Any]:
        """Полный анализ структуры проекта"""
        logger.info(f"Анализ проекта: {self.project_path}")
        
        result = {
            "project_path": str(self.project_path),
            "routes": await self._analyze_routes(),
            "models": await self._analyze_models(),
            "services": await self._analyze_services(),
            "structure": await self._analyze_directory_structure(),
            "dependencies": await self._analyze_dependencies()
        }
        
        return result
    
    async def _analyze_routes(self) -> List[Dict[str, Any]]:
        """Анализ роутов (FastAPI, Flask, Django)"""
        routes = []
        
        # Поиск файлов с роутами
        route_patterns = [
            "**/routes/**/*.py",
            "**/api/**/*.py", 
            "**/views/**/*.py"
        ]
        
        for pattern in route_patterns:
            for file_path in self.project_path.rglob(pattern):
                if file_path.is_file():
                    file_routes = await self._extract_routes_from_file(file_path)
                    routes.extend(file_routes)
        
        logger.info(f"Найдено роутов: {len(routes)}")
        return routes
    
    async def _extract_routes_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Извлечение роутов из Python файла"""
        routes = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # FastAPI декораторы
            fastapi_patterns = [
                r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
                r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']'
            ]
            
            for pattern in fastapi_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    method = match.group(1).upper()
                    path = match.group(2)
                    
                    routes.append({
                        "file": str(file_path.relative_to(self.project_path)),
                        "method": method,
                        "path": path,
                        "type": "fastapi"
                    })
        
        except Exception as e:
            logger.error(f"Ошибка анализа роутов {file_path}: {e}")
        
        return routes
    
    async def _analyze_models(self) -> List[Dict[str, Any]]:
        """Анализ моделей БД (SQLAlchemy, Django ORM)"""
        models = []
        
        # Поиск файлов с моделями
        model_patterns = [
            "**/models/**/*.py",
            "**/domain/entities/**/*.py"
        ]
        
        for pattern in model_patterns:
            for file_path in self.project_path.rglob(pattern):
                if file_path.is_file():
                    file_models = await self._extract_models_from_file(file_path)
                    models.extend(file_models)
        
        logger.info(f"Найдено моделей: {len(models)}")
        return models
    
    async def _extract_models_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Извлечение моделей из Python файла"""
        models = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Проверка наследования от Base, Model и т.д.
                    is_model = any(
                        isinstance(base, ast.Name) and base.id in ['Base', 'Model', 'BaseModel']
                        for base in node.bases
                    )
                    
                    if is_model:
                        # Извлечение полей
                        fields = []
                        for item in node.body:
                            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                                field_name = item.target.id
                                field_type = ast.unparse(item.annotation) if item.annotation else "Unknown"
                                fields.append({
                                    "name": field_name,
                                    "type": field_type
                                })
                        
                        models.append({
                            "file": str(file_path.relative_to(self.project_path)),
                            "name": node.name,
                            "fields": fields,
                            "docstring": ast.get_docstring(node)
                        })
        
        except Exception as e:
            logger.error(f"Ошибка анализа моделей {file_path}: {e}")
        
        return models
    
    async def _analyze_services(self) -> List[Dict[str, Any]]:
        """Анализ сервисов и бизнес-логики"""
        services = []
        
        service_patterns = [
            "**/services/**/*.py",
            "**/business/**/*.py"
        ]
        
        for pattern in service_patterns:
            for file_path in self.project_path.rglob(pattern):
                if file_path.is_file():
                    services.append({
                        "file": str(file_path.relative_to(self.project_path)),
                        "name": file_path.stem,
                        "type": "service"
                    })
        
        logger.info(f"Найдено сервисов: {len(services)}")
        return services
    
    async def _analyze_directory_structure(self) -> Dict[str, Any]:
        """Анализ структуры директорий"""
        structure = {
            "total_files": 0,
            "total_dirs": 0,
            "by_extension": {},
            "main_directories": []
        }
        
        # Подсчёт файлов и директорий
        for item in self.project_path.rglob('*'):
            if item.is_file():
                structure["total_files"] += 1
                ext = item.suffix or "no_extension"
                structure["by_extension"][ext] = structure["by_extension"].get(ext, 0) + 1
            elif item.is_dir():
                structure["total_dirs"] += 1
        
        # Главные директории
        for item in self.project_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                structure["main_directories"].append(item.name)
        
        return structure
    
    async def _analyze_dependencies(self) -> Dict[str, List[str]]:
        """Анализ зависимостей между модулями"""
        dependencies = {}
        
        # Поиск импортов
        for file_path in self.project_path.rglob('*.py'):
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    tree = ast.parse(content)
                    imports = []
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imports.append(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                imports.append(node.module)
                    
                    if imports:
                        relative_path = str(file_path.relative_to(self.project_path))
                        dependencies[relative_path] = list(set(imports))
                
                except Exception as e:
                    logger.debug(f"Пропуск файла {file_path}: {e}")
        
        return dependencies

