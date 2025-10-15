"""
ChromaDB клиент для хранения векторных данных
"""
import logging
import yaml
import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

class ChromaClient:
    def __init__(self, host: str = "chromadb", port: int = 8000):
        self.host = host
        self.port = port
        self.client = None
        self.collection = None
        
    async def initialize(self):
        """Инициализация ChromaDB клиента"""
        try:
            self.client = chromadb.AsyncClient(
                host=self.host,
                port=self.port,
                settings=Settings(allow_reset=True)
            )
            
            # Получение или создание коллекции
            try:
                self.collection = await self.client.get_collection("project_brain")
            except:
                self.collection = await self.client.create_collection(
                    "project_brain",
                    metadata={"description": "Project Brain knowledge base"}
                )
            
            logger.info("ChromaDB клиент инициализирован успешно")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации ChromaDB: {e}")
            raise
    
    async def store_chunks(self, project: str, chunks: List[Dict[str, Any]]):
        """Сохранение чанков в ChromaDB"""
        try:
            if not chunks:
                return
            
            # Подготовка данных для ChromaDB
            embeddings = []
            documents = []
            metadatas = []
            ids = []
            
            for chunk in chunks:
                # TODO: Здесь должен быть вызов модели эмбеддингов
                # Пока используем заглушку - в реальности нужно использовать sentence-transformers
                embedding = [0.0] * 384  # Размер эмбеддинга для all-MiniLM-L6-v2
                
                embeddings.append(embedding)
                documents.append(chunk['content'])
                
                metadata = {
                    'project': project,
                    'file': chunk.get('file', ''),
                    'lines': chunk.get('lines', ''),
                    'type': chunk.get('type', ''),
                    'chunk_id': chunk.get('chunk_id', 0)
                }
                
                # Добавление дополнительных метаданных
                if 'class_name' in chunk:
                    metadata['class_name'] = chunk['class_name']
                if 'function_name' in chunk:
                    metadata['function_name'] = chunk['function_name']
                if 'section' in chunk:
                    metadata['section'] = chunk['section']
                
                metadatas.append(metadata)
                ids.append(f"{project}_{chunk.get('file', '')}_{chunk.get('chunk_id', 0)}")
            
            # Сохранение в ChromaDB
            await self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Сохранено {len(chunks)} чанков для проекта {project}")
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении чанков: {e}")
            raise
    
    async def get_project_config(self, project: str) -> Optional[Dict[str, Any]]:
        """Получение конфигурации проекта"""
        try:
            config_path = "config/projects.yaml"
            if not os.path.exists(config_path):
                return None
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            projects = config.get("projects", [])
            return next((p for p in projects if p["name"] == project), None)
            
        except Exception as e:
            logger.error(f"Ошибка получения конфигурации проекта {project}: {e}")
            return None
    
    async def get_project_stats(self, project: str) -> Dict[str, Any]:
        """Получение статистики проекта"""
        try:
            # Подсчет чанков для проекта
            results = await self.collection.get(
                where={"project": project}
            )
            
            total_chunks = len(results['ids']) if results['ids'] else 0
            
            # Подсчет уникальных файлов
            files = set()
            file_types = {}
            
            if results['metadatas']:
                for metadata in results['metadatas']:
                    if 'file' in metadata:
                        files.add(metadata['file'])
                    if 'type' in metadata:
                        file_type = metadata['type']
                        file_types[file_type] = file_types.get(file_type, 0) + 1
            
            return {
                "total_chunks": total_chunks,
                "total_files": len(files),
                "file_types": file_types,
                "last_indexed": None  # TODO: Добавить отслеживание времени
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики проекта {project}: {e}")
            return {"total_chunks": 0, "total_files": 0, "file_types": {}}
    
    async def get_global_stats(self) -> Dict[str, Any]:
        """Получение глобальной статистики"""
        try:
            # Получение всех данных
            results = await self.collection.get()
            
            total_chunks = len(results['ids']) if results['ids'] else 0
            
            # Подсчет проектов
            projects = set()
            if results['metadatas']:
                for metadata in results['metadatas']:
                    if 'project' in metadata:
                        projects.add(metadata['project'])
            
            return {
                "total_chunks": total_chunks,
                "total_projects": len(projects),
                "total_files": 0,  # TODO: Подсчитать уникальные файлы
                "storage_size": 0,  # TODO: Подсчитать размер хранилища
                "last_updated": None
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения глобальной статистики: {e}")
            return {"total_chunks": 0, "total_projects": 0, "total_files": 0}
