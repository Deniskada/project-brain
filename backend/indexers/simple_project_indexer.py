"""
Упрощенный индексатор - обрабатывает файлы по одному для экономии памяти
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, AsyncGenerator
import yaml

logger = logging.getLogger(__name__)

class SimpleProjectIndexer:
    """Упрощенный индексатор с потоковой обработкой файлов"""
    
    def __init__(self, config_path: str = "config/projects.yaml"):
        self.config_path = config_path
        self.projects = []
        
    def load_config(self):
        """Загрузка конфигурации проектов"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.projects = config.get('projects', [])
                logger.info(f"Загружено {len(self.projects)} проектов")
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {e}")
            raise
    
    def should_index_file(self, file_path: str, project_config: Dict[str, Any]) -> bool:
        """Проверка, нужно ли индексировать файл"""
        # Проверка exclude паттернов
        exclude_patterns = project_config.get('exclude_patterns', [])
        for pattern in exclude_patterns:
            pattern_clean = pattern.replace('**/', '').replace('/**', '')
            if pattern_clean in file_path:
                return False
        
        # Проверка index паттернов
        index_patterns = project_config.get('index_patterns', [])
        for pattern in index_patterns:
            ext = pattern.replace('**/*.', '.')
            if file_path.endswith(ext):
                return True
        
        return False
    
    async def iter_project_files(
        self, 
        project_name: str,
        max_files: int = None,
        offset: int = 0
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Генератор файлов проекта (один за раз для экономии памяти)
        Args:
            max_files: Максимум файлов для обработки (None = все)
            offset: Пропустить первые N файлов
        Yields: Dict с информацией о файле
        """
        # Найти конфигурацию проекта
        project_config = None
        for proj in self.projects:
            if proj['name'] == project_name:
                project_config = proj
                break
        
        if not project_config:
            raise ValueError(f"Проект {project_name} не найден")
        
        project_path = project_config['path']
        logger.info(f"Сканирование: {project_name}, offset={offset}, max={max_files}")
        
        file_count = 0
        skipped = 0
        should_stop = False
        
        # Рекурсивный обход
        for root, dirs, files in os.walk(project_path):
            if should_stop:
                break
            
            # Фильтрация директорий
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', 'node_modules']]
            
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, project_path)
                
                if not self.should_index_file(relative_path, project_config):
                    if file_count == 0:  # Логируем первый отфильтрованный файл для отладки
                        logger.debug(f"Пропущен файл: {relative_path}")
                    continue
                
                # Пропуск файлов до offset
                if skipped < offset:
                    skipped += 1
                    continue
                
                file_count += 1
                
                yield {
                    'project': project_name,
                    'file_path': file_path,
                    'relative_path': relative_path,
                    'file_type': 'python' if file.endswith('.py') else 'markdown' if file.endswith('.md') else 'other'
                }
                
                # Логируем каждые 10 файлов
                if file_count % 10 == 0:
                    logger.info(f"Найдено {file_count} файлов... (последний: {relative_path})")
                
                # Ограничение по количеству файлов
                if max_files and file_count >= max_files:
                    logger.info(f"Достигнут лимит: {max_files} файлов")
                    should_stop = True
                    break
        
        logger.info(f"Всего найдено файлов: {file_count}")

