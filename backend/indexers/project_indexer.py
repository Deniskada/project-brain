"""
Индексатор проекта для загрузки кода в ChromaDB
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Any
import yaml
from .python_indexer import PythonIndexer
from .markdown_indexer import MarkdownIndexer

logger = logging.getLogger(__name__)

class ProjectIndexer:
    """Индексатор для загрузки всего проекта в векторную БД"""
    
    def __init__(self, config_path: str = "config/projects.yaml"):
        self.config_path = config_path
        self.python_indexer = PythonIndexer()
        self.markdown_indexer = MarkdownIndexer()
        self.projects = []
        
    def load_config(self):
        """Загрузка конфигурации проектов"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.projects = config.get('projects', [])
                logger.info(f"Загружено {len(self.projects)} проектов из конфигурации")
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {e}")
            raise
    
    def should_index_file(self, file_path: str, project_config: Dict[str, Any]) -> bool:
        """Проверка, нужно ли индексировать файл"""
        # Проверка exclude паттернов
        exclude_patterns = project_config.get('exclude_patterns', [])
        for pattern in exclude_patterns:
            if pattern.replace('**/', '').replace('/**', '') in file_path:
                return False
        
        # Проверка index паттернов
        index_patterns = project_config.get('index_patterns', [])
        for pattern in index_patterns:
            ext = pattern.replace('**/*.', '.')
            if file_path.endswith(ext):
                return True
        
        return False
    
    async def index_project(self, project_name: str) -> Dict[str, Any]:
        """Индексация одного проекта"""
        # Найти конфигурацию проекта
        project_config = None
        for proj in self.projects:
            if proj['name'] == project_name:
                project_config = proj
                break
        
        if not project_config:
            raise ValueError(f"Проект {project_name} не найден в конфигурации")
        
        project_path = project_config['path']
        logger.info(f"Начало индексации проекта: {project_name} ({project_path})")
        
        chunks = []
        stats = {
            'total_files': 0,
            'python_files': 0,
            'markdown_files': 0,
            'total_chunks': 0,
            'errors': []
        }
        
        # Рекурсивный обход директорий
        for root, dirs, files in os.walk(project_path):
            # Фильтрация директорий
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', 'node_modules']]
            
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, project_path)
                
                if not self.should_index_file(relative_path, project_config):
                    continue
                
                stats['total_files'] += 1
                
                try:
                    # Python файлы
                    if file.endswith('.py'):
                        file_chunks = await self.python_indexer.index_file(file_path)
                        for chunk in file_chunks:
                            chunk['project'] = project_name
                            chunk['file'] = relative_path
                        chunks.extend(file_chunks)
                        stats['python_files'] += 1
                    
                    # Markdown файлы
                    elif file.endswith('.md'):
                        file_chunks = await self.markdown_indexer.index_file(file_path)
                        for chunk in file_chunks:
                            chunk['project'] = project_name
                            chunk['file'] = relative_path
                        chunks.extend(file_chunks)
                        stats['markdown_files'] += 1
                
                except Exception as e:
                    error_msg = f"Ошибка индексации {relative_path}: {str(e)}"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)
        
        stats['total_chunks'] = len(chunks)
        logger.info(f"Индексация завершена: {stats}")
        
        return {
            'chunks': chunks,
            'stats': stats
        }
    
    def index_all_projects(self) -> Dict[str, Any]:
        """Индексация всех проектов из конфигурации"""
        self.load_config()
        
        all_chunks = []
        all_stats = {}
        
        for project in self.projects:
            project_name = project['name']
            try:
                result = self.index_project(project_name)
                all_chunks.extend(result['chunks'])
                all_stats[project_name] = result['stats']
            except Exception as e:
                logger.error(f"Ошибка индексации проекта {project_name}: {e}")
                all_stats[project_name] = {'error': str(e)}
        
        return {
            'chunks': all_chunks,
            'stats': all_stats
        }

