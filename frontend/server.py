#!/usr/bin/env python3
"""
Простой HTTP сервер для раздачи статики фронтенда
"""
import http.server
import socketserver
import os
import sys
from pathlib import Path

# Порт для фронтенда
PORT = 8080

# Директория со статикой
FRONTEND_DIR = Path(__file__).parent

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)
    
    def end_headers(self):
        # Добавляем CORS заголовки для API запросов
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        # Обработка preflight запросов
        self.send_response(200)
        self.end_headers()

def main():
    os.chdir(FRONTEND_DIR)
    
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"🚀 Frontend server запущен на http://localhost:{PORT}")
        print(f"📁 Директория: {FRONTEND_DIR}")
        print(f"🌐 Откройте: http://localhost:{PORT}/chat.html")
        print("Нажмите Ctrl+C для остановки")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Сервер остановлен")

if __name__ == "__main__":
    main()
