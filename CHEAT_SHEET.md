# 🚀 Secret House - Cheat Sheet

## Быстрый старт (5 минут)

### 1. Подготовка
```bash
cd /Users/a/secret-house-booking-bot

# Проверка готовности
./check_ready_simple.sh
```

### 2. Настройка окружения
```bash
# Создать .env файл
cp .env.docker.example .env

# Обязательно изменить:
# - TELEGRAM_TOKEN=your_token
# - BACKEND_API_KEY=random_32_chars
# - ADMIN_CHAT_ID=your_chat_id
```

### 3. Запуск

**Вариант A - Docker (рекомендуется):**
```bash
docker-compose up --build
```

**Вариант B - Локально:**
```bash
# Terminal 1
export ENV=debug
python backend/main.py

# Terminal 2
export ENV=debug
python telegram_bot/main.py
```

---

## Частые команды

### Docker
```bash
# Запуск
docker-compose up -d

# Логи
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs -f telegram_bot

# Остановка
docker-compose down

# Пересборка
docker-compose up --build
```

### Проверка здоровья
```bash
# Backend API
curl http://localhost:8000/health

# API документация
open http://localhost:8000/docs

# Или
curl http://localhost:8000/
```

### База данных
```bash
# Применить миграции
python -m alembic upgrade head

# Откатить миграцию
python -m alembic downgrade -1

# Создать новую миграцию
python -m alembic revision --autogenerate -m "описание"
```

### Redis
```bash
# Проверка
redis-cli ping

# Очистить все ключи
redis-cli FLUSHALL

# Посмотреть ключи
redis-cli KEYS "telegram:*"
```

---

## Структура проекта

```
secret-house-booking-bot/
├── backend/              # FastAPI Backend API
│   ├── main.py          # Точка входа
│   ├── api/v1/routers/  # REST endpoints
│   └── config/          # Конфигурация
├── telegram_bot/        # Telegram Bot UI
│   ├── main.py         # Точка входа
│   ├── handlers/       # 13 хендлеров
│   └── client/         # BackendAPIClient
├── db/                 # Database models
├── alembic/            # Миграции
└── docs/               # Документация
```

---

## API Endpoints (основные)

### Bookings
```bash
GET    /api/v1/bookings              # Все брони
GET    /api/v1/bookings/{id}         # Одна бронь
POST   /api/v1/bookings              # Создать
PATCH  /api/v1/bookings/{id}         # Обновить
DELETE /api/v1/bookings/{id}         # Отменить
```

### Users
```bash
GET    /api/v1/users                 # Все пользователи
GET    /api/v1/users/{id}            # Один пользователь
POST   /api/v1/users                 # Создать
PATCH  /api/v1/users/{id}            # Обновить
```

### Promocodes
```bash
GET    /api/v1/promocodes            # Все промокоды
POST   /api/v1/promocodes            # Создать
POST   /api/v1/promocodes/validate   # Проверить
```

### Availability
```bash
GET    /api/v1/availability/check    # Проверить даты
GET    /api/v1/availability/month    # Месяц доступности
```

---

## Telegram Bot команды

### Пользовательские
- `/start` - Главное меню

### Администраторские
- `/booking_list` - Управление бронями
- `/change_password` - Сменить пароль
- `/broadcast` - Рассылка всем
- `/broadcast_with_bookings` - Рассылка с бронями
- `/broadcast_without_bookings` - Рассылка без броней
- `/create_promocode` - Создать промокод
- `/list_promocodes` - Список промокодов
- `/users_without_chat_id` - Статистика

---

## Troubleshooting

### Backend не запускается
```bash
# Проверить порт
lsof -i :8000
kill $(lsof -t -i:8000)

# Проверить БД
rm data/the_secret_house.db-wal
rm data/the_secret_house.db-shm
python -m alembic upgrade head
```

### Bot не подключается
```bash
# Проверить Backend
curl http://localhost:8000/health

# Проверить переменные
echo $BACKEND_API_URL
echo $BACKEND_API_KEY
```

### Redis ошибки
```bash
# Запустить Redis
redis-server

# Или через Docker
docker run -d -p 6379:6379 redis:7-alpine
```

---

## Полезные скрипты

### Тестирование
```bash
# Системный тест
python3 test_system.py

# Проверка готовности
./check_ready_simple.sh
```

### Генерация данных
```bash
# API ключ
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Случайная строка
openssl rand -base64 32
```

---

## Environment Variables

### Обязательные
```bash
TELEGRAM_TOKEN=         # От @BotFather
BACKEND_API_KEY=        # Случайная строка
ADMIN_CHAT_ID=          # Ваш Telegram ID
BACKEND_API_URL=        # http://localhost:8000
DATABASE_URL=           # sqlite:///./data/db.db
```

### Опциональные
```bash
GOOGLE_CREDENTIALS=     # Путь к credentials.json
CALENDAR_ID=            # Google Calendar ID
GPT_KEY=                # OpenAI API key
REDIS_HOST=             # localhost
REDIS_PORT=             # 6379
```

---

## Git команды

```bash
# Статус
git status

# Коммит
git add .
git commit -m "описание"

# Пуш
git push origin main

# Новая ветка
git checkout -b feature/new-feature
```

---

## Мониторинг

### Логи
```bash
# Docker
docker-compose logs -f --tail=50

# Локально
tail -f logs/backend.log
tail -f logs/bot.log
```

### Метрики
```bash
# Количество активных броней
curl http://localhost:8000/api/v1/bookings | jq 'length'

# Количество пользователей
curl http://localhost:8000/api/v1/users | jq 'length'
```

---

## Ссылки на документацию

- 📘 [README.md](README.md) - Общее описание
- 🚀 [QUICK_START.md](QUICK_START.md) - Детальная инструкция
- 📋 [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Чеклист деплоя
- 📊 [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) - Отчет рефакторинга
- 🎉 [FINAL_REPORT.md](FINAL_REPORT.md) - Финальный отчет

---

## Контакты

**API Docs:** http://localhost:8000/docs
**Health Check:** http://localhost:8000/health
**ReDoc:** http://localhost:8000/redoc

---

*Последнее обновление: 27.11.2025*
