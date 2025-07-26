#!/usr/bin/env python3
"""
Скрипт для запуска LLM Gateway сервера
"""

import uvicorn
import os
from dotenv import load_dotenv

def main():
    """Запуск сервера с правильными настройками"""
    print("🚀 Запуск LLM Gateway сервера...")
    
    # Загружаем переменные окружения
    load_dotenv()
    
    # Настройки сервера
    host = os.getenv('HOST', '0.0.0.0')  # По умолчанию на всех интерфейсах
    port = int(os.getenv('PORT', 8000))   # По умолчанию порт 8000
    reload = os.getenv('DEBUG', 'false').lower() == 'true'  # Автоперезагрузка в debug режиме
    
    print(f"📊 Настройки сервера:")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Debug: {reload}")
    print(f"   URL: http://{host}:{port}")
    
    if host == '0.0.0.0':
        print("🌐 Сервер будет доступен на всех сетевых интерфейсах")
        print("   Локально: http://localhost:8000")
        print("   В сети: http://<ваш_ip>:8000")
    else:
        print(f"🔒 Сервер будет доступен только на {host}")
    
    print("\n" + "=" * 50)
    print("🚀 Запуск сервера...")
    print("   Нажмите Ctrl+C для остановки")
    print("=" * 50)
    
    # Запускаем сервер
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    main() 