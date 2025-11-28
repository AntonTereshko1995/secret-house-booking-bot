# Quick Start Guide - Микросервисная архитектура

## 🚀 Запуск проекта

### Предварительные требования
- Python 3.9+
- Redis Server
- PostgreSQL или SQLite

---

## 1️⃣ Запуск Backend API

```bash
# Перейти в директорию backend
cd /Users/a/secret-house-booking-bot

# Установить зависимости (если еще не установлены)
pip install -r requirements.txt

# Установить переменные окружения
export ENV=debug

# Запустить Backend API
python backend/main.py
```

Backend API будет доступен на `http://localhost:8000`

**Проверка здоровья API:**
```bash
curl http://localhost:8000/health
```

---

## 2️⃣ Запуск Telegram Bot

**В новом терминале:**

```bash
# Перейти в директорию проекта
cd /Users/a/secret-house-booking-bot

# Установить переменные окружения
export ENV=debug

# Запустить Telegram Bot
python telegram_bot/main.py
```

При запуске бот автоматически проверит доступность Backend API.

---

## 📁 Структура переменных окружения

### `.env.debug` (для разработки):
```env
# Telegram
TELEGRAM_TOKEN=your_telegram_bot_token

# Backend API
BACKEND_API_URL=http://localhost:8000

# Admin
ADMIN_CHAT_ID=your_admin_chat_id

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Database
DATABASE_URL=sqlite:///./test_the_secret_house.db
```

### `.env.production` (для продакшена):
```env
# Аналогично .env.debug, но с production значениями
BACKEND_API_URL=https://your-production-api.com
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

---

## 🐳 Запуск через Docker Compose

```bash
# Собрать и запустить все сервисы
docker-compose up --build

# Запустить в фоновом режиме
docker-compose up -d

# Остановить все сервисы
docker-compose down
```

**Сервисы:**
- Backend API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

---

## 🔍 Проверка статуса

### Backend API
```bash
# Health check
curl http://localhost:8000/health

# Список всех endpoints
curl http://localhost:8000/docs
```

### Telegram Bot
Отправьте `/start` в телеграм-боте

---

## 🛠️ Разработка

### Добавление нового endpoint в Backend API

1. Создать модель в `backend/models/`
2. Добавить endpoint в `backend/routers/`
3. Обновить `BackendAPIClient` в `telegram_bot/client/backend_api.py`

### Добавление нового хендлера в Bot

1. Создать файл в `telegram_bot/handlers/`
2. Использовать `BackendAPIClient` для всех операций с данными
3. Зарегистрировать хендлер в `telegram_bot/main.py`

**Пример:**
```python
from telegram_bot.client.backend_api import BackendAPIClient, APIError

async def my_handler(update, context):
    api_client = BackendAPIClient()
    try:
        data = await api_client.some_method()
    except APIError as e:
        logger.error(f"API Error: {e}")
```

---

## 📊 Миграции БД

```bash
# Создать новую миграцию
python -m alembic revision --autogenerate -m "description"

# Применить миграции
python -m alembic upgrade head

# Откатить миграцию
python -m alembic downgrade -1
```

---

## 🧪 Тестирование

### Backend API
```bash
pytest backend/tests/
```

### Integration Tests
```bash
# Убедитесь что Backend и Bot запущены
pytest tests/integration/
```

---

## 📝 Логи

### Backend API
```bash
tail -f logs/backend.log
```

### Telegram Bot
```bash
tail -f logs/bot.log
```

---

## ⚠️ Troubleshooting

### Bot не подключается к Backend
1. Проверьте что Backend запущен: `curl http://localhost:8000/health`
2. Проверьте `BACKEND_API_URL` в `.env.debug`
3. Проверьте логи Backend

### Redis ошибки
1. Запустите Redis: `redis-server`
2. Проверьте подключение: `redis-cli ping`
3. Проверьте `REDIS_HOST` и `REDIS_PORT` в конфиге

### Database ошибки
1. Примените миграции: `python -m alembic upgrade head`
2. Проверьте `DATABASE_URL` в конфиге
3. Для PostgreSQL: убедитесь что БД создана

---

## 🔗 Полезные ссылки

- [Backend API Docs](http://localhost:8000/docs) - Swagger UI
- [Backend API ReDoc](http://localhost:8000/redoc) - ReDoc
- [Alembic Docs](https://alembic.sqlalchemy.org/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [python-telegram_bot Docs](https://docs.python-telegram_bot.org/)

---

**Проект готов к работе! 🎉**
