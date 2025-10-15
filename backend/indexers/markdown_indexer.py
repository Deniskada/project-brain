"""
Индексатор Markdown файлов
"""
import os
import re
import logging
from typing import List, Dict, Any, Optional
import fnmatch

logger = logging.getLogger(__name__)

class MarkdownIndexer:
    def __init__(self):
        self.chunk_size = 1000  # Размер чанка в символах
        self.overlap = 200      # Перекрытие между чанками
    
    async def find_files(
        self, 
        project_path: str, 
        include_patterns: List[str],
        exclude_patterns: List[str]
    ) -> List[str]:
        """Поиск Markdown файлов для индексации"""
        files = []
        
        for root, dirs, filenames in os.walk(project_path):
            # Исключение директорий
            dirs[:] = [d for d in dirs if not any(
                self._matches_pattern(d, exclude_patterns) for exclude in exclude_patterns
            )]
            
            for filename in filenames:
                if filename.endswith('.md'):
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
        """Индексация одного Markdown файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            chunks = []
            
            # Разбиение на секции по заголовкам
            sections = self._split_by_headers(content)
            
            for i, section in enumerate(sections):
                if len(section['content'].strip()) < 50:  # Пропускаем слишком короткие секции
                    continue
                
                # Парсинг start_line, end_line из lines
                lines_str = section.get('lines', '0-0')
                try:
                    start_line, end_line = map(int, lines_str.split('-'))
                except:
                    start_line, end_line = 0, 0
                
                # Дополнительное разбиение на чанки если секция слишком большая
                sub_chunks = self._split_into_chunks(section['content'])
                
                for j, chunk_content in enumerate(sub_chunks):
                    chunk = {
                        "content": chunk_content,
                        "file": file_path,
                        "lines": lines_str,
                        "start_line": start_line,
                        "end_line": end_line,
                        "type": "markdown",
                        "section": section.get('header', ''),
                        "chunk_id": hash(f"{file_path}_{i}_{j}")
                    }
                    chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Ошибка индексации файла {file_path}: {e}")
            return []
    
    def _split_by_headers(self, content: str) -> List[Dict[str, Any]]:
        """Разбиение контента по заголовкам"""
        sections = []
        lines = content.split('\n')
        current_section = {'content': '', 'header': '', 'lines': ''}
        start_line = 1
        
        for i, line in enumerate(lines, 1):
            # Проверка на заголовок
            if re.match(r'^#+\s+', line):
                # Сохраняем предыдущую секцию
                if current_section['content'].strip():
                    current_section['lines'] = f"{start_line}-{i-1}"
                    sections.append(current_section)
                
                # Начинаем новую секцию
                current_section = {
                    'content': line + '\n',
                    'header': line.strip(),
                    'lines': ''
                }
                start_line = i
            else:
                current_section['content'] += line + '\n'
        
        # Добавляем последнюю секцию
        if current_section['content'].strip():
            current_section['lines'] = f"{start_line}-{len(lines)}"
            sections.append(current_section)
        
        return sections
    
    def _split_into_chunks(self, content: str) -> List[str]:
        """Разбиение контента на чанки"""
        if len(content) <= self.chunk_size:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + self.chunk_size
            
            if end >= len(content):
                chunks.append(content[start:])
                break
            
            # Ищем ближайший конец предложения или абзаца
            chunk_end = content.rfind('\n\n', start, end)
            if chunk_end == -1:
                chunk_end = content.rfind('\n', start, end)
            if chunk_end == -1:
                chunk_end = content.rfind('.', start, end)
            if chunk_end == -1:
                chunk_end = end
            
            chunks.append(content[start:chunk_end])
            start = chunk_end - self.overlap if chunk_end > self.overlap else chunk_end
        
        return chunks
