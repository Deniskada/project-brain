"""
FastAPI приложение для Project Brain
"""
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
from typing import Dict, Any

from .routes import query, index, projects, stats, context_rules, documentation, webhook

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Project Brain API",
    description="Система управления знаниями проекта на базе локальной LLM",
    version="1.0.0"
)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутов
app.include_router(query.router, prefix="/api", tags=["query"])
app.include_router(index.router, prefix="/api", tags=["index"])
app.include_router(projects.router, prefix="/api", tags=["projects"])
app.include_router(stats.router, prefix="/api", tags=["stats"])
app.include_router(context_rules.router, prefix="/api", tags=["context-rules"])
app.include_router(documentation.router, prefix="/api/documentation", tags=["documentation"])
app.include_router(webhook.router, prefix="/api/webhook", tags=["webhook"])

# Статические файлы
if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Главная страница с чат-интерфейсом"""
    try:
        with open("frontend/chat.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
            <head><title>Project Brain</title></head>
            <body>
                <h1>Project Brain API</h1>
                <p>API работает! Документация доступна по адресу <a href="/docs">/docs</a></p>
            </body>
        </html>
        """)

@app.get("/chat", response_class=HTMLResponse)
async def chat():
    """Чат-интерфейс"""
    try:
        with open("frontend/chat.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Чат не найден</h1>")

@app.get("/docs", response_class=HTMLResponse)
async def docs():
    """Интерфейс документации"""
    try:
        with open("frontend/docs.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Документация не найдена</h1>")

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy", "service": "project-brain"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
