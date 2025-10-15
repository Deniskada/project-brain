"""
API роуты для управления проектами
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import yaml
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/projects")
async def get_projects() -> List[Dict[str, Any]]:
    """Получение списка всех проектов"""
    try:
        config_path = "config/projects.yaml"
        if not os.path.exists(config_path):
            return []
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        projects = config.get("projects", [])
        
        # Добавление статуса индексации для каждого проекта
        for project in projects:
            project["status"] = "configured"
            # TODO: Добавить проверку реального статуса индексации
        
        return projects
        
    except Exception as e:
        logger.error(f"Ошибка при получении списка проектов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения проектов: {str(e)}")

@router.get("/projects/{project_name}")
async def get_project(project_name: str) -> Dict[str, Any]:
    """Получение информации о конкретном проекте"""
    try:
        config_path = "config/projects.yaml"
        if not os.path.exists(config_path):
            raise HTTPException(status_code=404, detail="Конфигурация проектов не найдена")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        projects = config.get("projects", [])
        project = next((p for p in projects if p["name"] == project_name), None)
        
        if not project:
            raise HTTPException(status_code=404, detail=f"Проект {project_name} не найден")
        
        return project
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении проекта {project_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения проекта: {str(e)}")
