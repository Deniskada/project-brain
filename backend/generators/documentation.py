"""
Генератор документации для разных аудиторий
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class DocumentationGenerator:
    """Генерация документации на основе анализа проекта"""
    
    def __init__(self, rag_engine):
        self.rag = rag_engine
    
    async def generate_for_developers(self, project_data: Dict[str, Any]) -> str:
        """Генерация документации для разработчиков"""
        logger.info("Генерация документации для разработчиков")
        
        doc = []
        doc.append("# 🛠️ Документация для разработчиков\n")
        doc.append(f"**Дата генерации:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        doc.append(f"**Проект:** {project_data.get('project_path', 'N/A')}\n\n")
        
        # API Reference
        doc.append("## 📡 API Reference\n")
        routes = project_data.get('routes', [])
        if routes:
            doc.append(f"**Всего эндпоинтов:** {len(routes)}\n\n")
            
            # Группировка по методам
            by_method = {}
            for route in routes:
                method = route['method']
                by_method.setdefault(method, []).append(route)
            
            for method, routes_list in sorted(by_method.items()):
                doc.append(f"### {method}\n")
                for route in routes_list:
                    doc.append(f"- `{method} {route['path']}` - {route['file']}\n")
                doc.append("\n")
        
        # Database Schema
        doc.append("## 🗄️ Database Schema\n")
        models = project_data.get('models', [])
        if models:
            doc.append(f"**Всего моделей:** {len(models)}\n\n")
            for model in models:
                doc.append(f"### {model['name']}\n")
                if model.get('docstring'):
                    doc.append(f"{model['docstring']}\n")
                
                doc.append("**Поля:**\n")
                for field in model.get('fields', []):
                    doc.append(f"- `{field['name']}`: {field['type']}\n")
                doc.append("\n")
        
        # Architecture Overview
        doc.append("## 🏗️ Architecture Overview\n")
        structure = project_data.get('structure', {})
        doc.append(f"**Всего файлов:** {structure.get('total_files', 0)}\n")
        doc.append(f"**Всего директорий:** {structure.get('total_dirs', 0)}\n\n")
        
        doc.append("**Основные директории:**\n")
        for dir_name in structure.get('main_directories', []):
            doc.append(f"- `{dir_name}/`\n")
        doc.append("\n")
        
        # Services
        doc.append("## 🔧 Services\n")
        services = project_data.get('services', [])
        if services:
            doc.append(f"**Всего сервисов:** {len(services)}\n\n")
            for service in services:
                doc.append(f"- `{service['file']}`\n")
        
        return "".join(doc)
    
    async def generate_for_admins(self, project_data: Dict[str, Any]) -> str:
        """Генерация документации для администраторов"""
        logger.info("Генерация документации для администраторов")
        
        doc = []
        doc.append("# 🔧 Руководство администратора\n")
        doc.append(f"**Дата генерации:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        doc.append("## 🚀 Развертывание\n")
        doc.append("### Требования\n")
        doc.append("- Python 3.11+\n")
        doc.append("- Docker и Docker Compose\n")
        doc.append("- PostgreSQL 15+\n")
        doc.append("- Redis 7+\n\n")
        
        doc.append("### Быстрый старт\n")
        doc.append("```bash\n")
        doc.append("# 1. Клонирование репозитория\n")
        doc.append("git clone <repo_url>\n")
        doc.append("cd project\n\n")
        doc.append("# 2. Настройка окружения\n")
        doc.append("cp .env.example .env\n")
        doc.append("# Отредактируйте .env файл\n\n")
        doc.append("# 3. Запуск через Docker\n")
        doc.append("docker compose up -d\n")
        doc.append("```\n\n")
        
        doc.append("## ⚙️ Конфигурация\n")
        doc.append("### Переменные окружения\n")
        doc.append("- `DATABASE_URL` - URL подключения к БД\n")
        doc.append("- `REDIS_URL` - URL подключения к Redis\n")
        doc.append("- `SECRET_KEY` - секретный ключ приложения\n\n")
        
        doc.append("## 🔍 Мониторинг\n")
        doc.append("### Логи\n")
        doc.append("```bash\n")
        doc.append("# Просмотр логов\n")
        doc.append("docker compose logs -f\n")
        doc.append("```\n\n")
        
        doc.append("## 🛠️ Troubleshooting\n")
        doc.append("### Частые проблемы\n")
        doc.append("1. **Приложение не запускается**\n")
        doc.append("   - Проверьте переменные окружения\n")
        doc.append("   - Убедитесь, что БД доступна\n\n")
        
        return "".join(doc)
    
    async def generate_for_users(self, project_data: Dict[str, Any]) -> str:
        """Генерация документации для пользователей"""
        logger.info("Генерация документации для пользователей")
        
        doc = []
        doc.append("# 📖 Руководство пользователя\n")
        doc.append(f"**Дата генерации:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        doc.append("## 🎯 Введение\n")
        doc.append("Добро пожаловать! Это руководство поможет вам начать работу.\n\n")
        
        doc.append("## 🚀 Быстрый старт\n")
        doc.append("### Регистрация\n")
        doc.append("1. Перейдите на страницу регистрации\n")
        doc.append("2. Заполните форму\n")
        doc.append("3. Подтвердите email\n\n")
        
        doc.append("### Первые шаги\n")
        doc.append("1. Войдите в систему\n")
        doc.append("2. Настройте профиль\n")
        doc.append("3. Начните работу!\n\n")
        
        doc.append("## 💡 Основные функции\n")
        doc.append("### Работа с данными\n")
        doc.append("- Создание записей\n")
        doc.append("- Редактирование\n")
        doc.append("- Удаление\n\n")
        
        doc.append("## ❓ FAQ\n")
        doc.append("### Как сбросить пароль?\n")
        doc.append("Используйте функцию восстановления пароля на странице входа.\n\n")
        
        doc.append("### Где найти помощь?\n")
        doc.append("Обратитесь в службу поддержки через форму обратной связи.\n\n")
        
        return "".join(doc)
    
    async def generate_all(self, project_data: Dict[str, Any]) -> Dict[str, str]:
        """Генерация всей документации"""
        return {
            "developers": await self.generate_for_developers(project_data),
            "admins": await self.generate_for_admins(project_data),
            "users": await self.generate_for_users(project_data)
        }

