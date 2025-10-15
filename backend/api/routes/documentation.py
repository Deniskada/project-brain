"""
API роуты для генерации документации
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

from ...analyzers.project_structure import ProjectStructureAnalyzer
from ...generators.documentation import DocumentationGenerator
from ...rag.engine import RAGEngine

router = APIRouter()
logger = logging.getLogger(__name__)

class GenerateDocsRequest(BaseModel):
    project: str = "staffprobot"
    audiences: Optional[list] = None  # ["developers", "admins", "users"]

class GenerateDocsResponse(BaseModel):
    status: str
    project: str
    documentation: Dict[str, str]
    analysis: Optional[Dict[str, Any]] = None

# Глобальные экземпляры
rag_engine: Optional[RAGEngine] = None
doc_generator: Optional[DocumentationGenerator] = None

async def get_rag_engine() -> RAGEngine:
    """Получение RAG engine"""
    global rag_engine
    if rag_engine is None:
        rag_engine = RAGEngine()
        await rag_engine.initialize()
    return rag_engine

@router.post("/generate", response_model=GenerateDocsResponse)
async def generate_documentation(request: GenerateDocsRequest):
    """
    Генерация документации для проекта
    """
    try:
        logger.info(f"Генерация документации для проекта: {request.project}")
        
        # Определение пути к проекту
        project_paths = {
            "staffprobot": "/projects/staffprobot"
        }
        
        project_path = project_paths.get(request.project)
        if not project_path:
            raise HTTPException(
                status_code=404,
                detail=f"Проект {request.project} не найден"
            )
        
        # Анализ структуры проекта
        analyzer = ProjectStructureAnalyzer(project_path)
        project_data = await analyzer.analyze()
        
        logger.info(f"Анализ завершён: {len(project_data.get('routes', []))} роутов, "
                   f"{len(project_data.get('models', []))} моделей")
        
        # Генерация документации
        rag = await get_rag_engine()
        generator = DocumentationGenerator(rag)
        
        audiences = request.audiences or ["developers", "admins", "users"]
        documentation = {}
        
        if "developers" in audiences:
            documentation["developers"] = await generator.generate_for_developers(project_data)
        
        if "admins" in audiences:
            documentation["admins"] = await generator.generate_for_admins(project_data)
        
        if "users" in audiences:
            documentation["users"] = await generator.generate_for_users(project_data)
        
        logger.info(f"Документация сгенерирована для {len(documentation)} аудиторий")
        
        return GenerateDocsResponse(
            status="success",
            project=request.project,
            documentation=documentation,
            analysis={
                "routes_count": len(project_data.get('routes', [])),
                "models_count": len(project_data.get('models', [])),
                "services_count": len(project_data.get('services', [])),
                "total_files": project_data.get('structure', {}).get('total_files', 0)
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка генерации документации: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")

@router.get("/test")
async def test_documentation():
    """Тестовый endpoint"""
    return {"message": "Documentation API работает!", "status": "ok"}

