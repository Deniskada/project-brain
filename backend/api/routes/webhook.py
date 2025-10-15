"""
API роуты для webhook автообновления
"""
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Header
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import hashlib
import hmac

router = APIRouter()
logger = logging.getLogger(__name__)

class WebhookPayload(BaseModel):
    ref: Optional[str] = None
    repository: Optional[Dict[str, Any]] = None
    commits: Optional[list] = None

async def process_github_push(payload: Dict[str, Any]):
    """
    Обработка push события от GitHub
    """
    try:
        repo_name = payload.get('repository', {}).get('name', 'unknown')
        ref = payload.get('ref', '')
        commits_count = len(payload.get('commits', []))
        
        logger.info(f"🔄 GitHub Push: {repo_name}, ref: {ref}, commits: {commits_count}")
        
        # Определяем, нужно ли переиндексировать
        if 'main' in ref or 'master' in ref:
            logger.info(f"🚀 Запуск переиндексации для {repo_name}")
            
            # Импортируем здесь чтобы избежать циклических импортов
            from ...indexers.simple_project_indexer import SimpleProjectIndexer
            from ...indexers.python_indexer import PythonIndexer
            from ...indexers.markdown_indexer import MarkdownIndexer
            from ...rag.engine import RAGEngine
            import subprocess
            
            # Определяем проект по имени репозитория
            project_map = {
                'staffprobot': 'staffprobot',
                'project-brain': 'project-brain'
            }
            
            project_name = project_map.get(repo_name.lower())
            
            if project_name:
                # Получаем путь к проекту
                from ...indexers.simple_project_indexer import SimpleProjectIndexer
                indexer = SimpleProjectIndexer()
                project_config = indexer.get_project_config(project_name)
                
                if not project_config:
                    logger.error(f"❌ Конфигурация проекта {project_name} не найдена")
                    return
                
                project_path = project_config.get('path')
                git_url = project_config.get('git_url')
                
                # ШАГ 1: Обновление кода из git
                try:
                    logger.info(f"📥 Обновление кода: git pull в {project_path}")
                    
                    # git fetch origin
                    result = subprocess.run(
                        ['git', 'fetch', 'origin'],
                        cwd=project_path,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode != 0:
                        logger.error(f"❌ git fetch failed: {result.stderr}")
                        return
                    
                    # git pull origin main/master
                    branch = 'main' if 'main' in ref else 'master'
                    result = subprocess.run(
                        ['git', 'pull', 'origin', branch],
                        cwd=project_path,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    if result.returncode != 0:
                        logger.error(f"❌ git pull failed: {result.stderr}")
                        return
                    
                    logger.info(f"✅ Код обновлён: {result.stdout.strip()}")
                    
                except subprocess.TimeoutExpired:
                    logger.error("❌ Git операция timeout")
                    return
                except Exception as e:
                    logger.error(f"❌ Ошибка git pull: {e}")
                    return
                
                # ШАГ 2: Переиндексация
                logger.info(f"📚 Начинаем индексацию проекта: {project_name}")
                
                # Инициализация
                project_indexer = SimpleProjectIndexer()
                python_indexer = PythonIndexer()
                markdown_indexer = MarkdownIndexer()
                rag_engine = RAGEngine()
                await rag_engine.initialize()
                
                stats = {
                    'total_files': 0,
                    'total_chunks': 0,
                    'errors': 0
                }
                
                # Индексация
                async for file_info in project_indexer.iter_project_files(project_name):
                    try:
                        file_path = file_info['file_path']
                        file_type = file_info['file_type']
                        relative_path = file_info['relative_path']
                        
                        stats['total_files'] += 1
                        
                        # Индексация файла
                        chunks = []
                        if file_type == 'python':
                            chunks = await python_indexer.index_file(file_path)
                        elif file_type == 'markdown':
                            chunks = await markdown_indexer.index_file(file_path)
                        
                        # Загрузка чанков
                        for chunk in chunks:
                            doc_type = python_indexer._classify_doc_type(relative_path) if file_type == 'python' else 'documentation'
                            
                            await rag_engine.store_document(
                                project=project_name,
                                content=chunk['content'],
                                metadata={
                                    'file': relative_path,
                                    'type': chunk['type'],
                                    'doc_type': doc_type,
                                    'start_line': chunk.get('start_line', 0),
                                    'end_line': chunk.get('end_line', 0),
                                    'lines': chunk.get('lines', '0-0'),
                                    'project': project_name,
                                    'chunk_id': chunk.get('chunk_id', hash(chunk['content'][:100]))
                                }
                            )
                            stats['total_chunks'] += 1
                    
                    except Exception as e:
                        stats['errors'] += 1
                        logger.error(f"Ошибка обработки файла: {e}")
                
                logger.info(f"✅ Индексация завершена: {stats}")
                
                # TODO: Отправить уведомление в Telegram
                
            else:
                logger.warning(f"⚠️ Проект {repo_name} не настроен для автоиндексации")
        
        else:
            logger.info(f"ℹ️ Пропускаем индексацию для ref: {ref}")
    
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}", exc_info=True)

def verify_github_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    """
    Проверка подписи webhook от GitHub
    """
    if not signature:
        return False
    
    # GitHub отправляет подпись в формате "sha256=..."
    hash_algorithm, github_signature = signature.split('=')
    
    # Вычисляем HMAC
    mac = hmac.new(secret.encode(), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = mac.hexdigest()
    
    # Сравниваем
    return hmac.compare_digest(expected_signature, github_signature)

@router.post("/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: Optional[str] = Header(None),
    x_github_event: Optional[str] = Header(None)
):
    """
    Webhook для получения событий от GitHub
    
    Настройка в GitHub:
    1. Settings → Webhooks → Add webhook
    2. Payload URL: https://your-domain.com/api/webhook/github
    3. Content type: application/json
    4. Secret: установите секрет и добавьте в .env как GITHUB_WEBHOOK_SECRET
    5. Events: Just the push event
    """
    try:
        # Читаем тело запроса
        body = await request.body()
        payload = await request.json()
        
        # Логируем событие
        logger.info(f"📥 GitHub webhook: event={x_github_event}, repo={payload.get('repository', {}).get('name', 'unknown')}")
        
        # Проверка подписи (если настроен секрет)
        import os
        webhook_secret = os.getenv('GITHUB_WEBHOOK_SECRET')
        if webhook_secret:
            if not verify_github_signature(body, x_hub_signature_256, webhook_secret):
                logger.warning("❌ Invalid webhook signature")
                raise HTTPException(status_code=401, detail="Invalid signature")
        else:
            logger.warning("⚠️ GITHUB_WEBHOOK_SECRET не установлен - webhook НЕ защищён!")
        
        # Обрабатываем только push события
        if x_github_event == 'push':
            # Запускаем обработку в фоне
            background_tasks.add_task(process_github_push, payload)
            
            return {
                "status": "accepted",
                "message": "Push event will be processed",
                "ref": payload.get('ref'),
                "commits": len(payload.get('commits', []))
            }
        
        elif x_github_event == 'ping':
            # Ping событие при настройке webhook
            return {
                "status": "ok",
                "message": "Webhook configured successfully"
            }
        
        else:
            logger.info(f"ℹ️ Ignoring event: {x_github_event}")
            return {
                "status": "ignored",
                "message": f"Event {x_github_event} is not processed"
            }
    
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test")
async def test_webhook():
    """Тестовый endpoint"""
    return {
        "status": "ok",
        "message": "Webhook API работает!",
        "endpoints": {
            "github": "/api/webhook/github"
        }
    }

@router.post("/manual-reindex/{project_name}")
async def manual_reindex(project_name: str, background_tasks: BackgroundTasks):
    """
    Ручной запуск переиндексации
    """
    logger.info(f"🔄 Ручная переиндексация проекта: {project_name}")
    
    # Создаём фейковый payload для переиспользования логики
    fake_payload = {
        'ref': 'refs/heads/main',
        'repository': {'name': project_name},
        'commits': []
    }
    
    background_tasks.add_task(process_github_push, fake_payload)
    
    return {
        "status": "accepted",
        "message": f"Reindexing {project_name} started in background"
    }

