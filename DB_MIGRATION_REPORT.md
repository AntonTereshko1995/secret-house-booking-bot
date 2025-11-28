# 🗄️ Отчет о переносе папки db/ в backend/

**Дата:** 27 ноября 2025

## ✅ Выполнено

### Перенесена папка `db/` → `backend/db/`

Папка `db/` с моделями базы данных была перенесена в `backend/db/`, что логично объединяет всю backend-специфичную логику.

---

## 📦 Что было перемещено

```
db/                          →  backend/db/
├── __init__.py             →  backend/db/__init__.py
├── database.py             →  backend/db/database.py
├── run_migrations.py       →  backend/db/run_migrations.py
└── models/                 →  backend/db/models/
    ├── base.py            →  backend/db/models/base.py
    ├── user.py            →  backend/db/models/user.py
    ├── booking.py         →  backend/db/models/booking.py
    ├── gift.py            →  backend/db/models/gift.py
    ├── promocode.py       →  backend/db/models/promocode.py
    └── decorator/         →  backend/db/models/decorator/
```

---

## 🔧 Обновленные импорты

### Backend

**Было:**
```python
from db.models.booking import BookingBase
from db.models.user import UserBase
from db.database import SessionLocal
from db.run_migrations import run_migrations
```

**Стало:**
```python
from backend.db.models.booking import BookingBase
from backend.db.models.user import UserBase
from backend.db.database import SessionLocal
from backend.db.run_migrations import run_migrations
```

### Alembic (миграции)

**Было:**
```python
from db.models.base import Base
from db.models.user import UserBase
from db.models.booking import BookingBase
```

**Стало:**
```python
from backend.db.models.base import Base
from backend.db.models.user import UserBase
from backend.db.models.booking import BookingBase
```

---

## 📊 Статистика изменений

### Обновленные файлы

**Backend:** ~15 файлов
- `backend/api/v1/routers/`: 6 файлов
- `backend/services/database/`: 4 файла
- `backend/models/`: 2 файла
- `backend/helpers/`: 1 файл
- `backend/main.py`: 1 файл
- `backend/api/v1/dependencies.py`: 1 файл

**Backend/db:** 5 файлов
- `backend/db/database.py`
- `backend/db/run_migrations.py`
- `backend/db/models/booking.py`
- `backend/db/models/gift.py`
- `backend/db/models/promocode.py`

**Alembic:** 3 файла
- `alembic/env.py`
- `alembic/versions/16c4e4787de0_base_migration.py`
- `alembic/versions/691bc97d7a18_initial_migration.py`

### Импорты заменено

- `from db.*` → `from backend.db.*`: ~26 мест
- `from src.*` → `from backend.*`: ~8 мест (в db и alembic)

---

## ✅ Проверки пройдены

### Синтаксис
```bash
✅ backend/main.py - OK
✅ backend/db/database.py - OK
✅ alembic/env.py - OK
```

### Импорты
```bash
✅ Нет оставшихся импортов из db (не backend.db)
✅ Нет оставшихся импортов из src в backend
✅ Нет оставшихся импортов из src в alembic
```

### Структура
```bash
✅ Папка db/ перенесена в backend/db/
✅ Старая папка db/ удалена
```

---

## 📁 Итоговая структура проекта

```
secret-house-booking-bot/
│
├── backend/                    # Backend API (FastAPI)
│   ├── api/v1/routers/        # REST endpoints
│   ├── config/                # Configuration
│   ├── db/                    # 📌 Database models (перенесено)
│   │   ├── database.py        # SQLAlchemy engine & sessions
│   │   ├── run_migrations.py # Migration runner
│   │   └── models/            # SQLAlchemy ORM models
│   │       ├── base.py
│   │       ├── user.py
│   │       ├── booking.py
│   │       ├── gift.py
│   │       ├── promocode.py
│   │       └── decorator/
│   ├── models/                # Pydantic models (для API)
│   ├── services/              # Business logic
│   └── main.py
│
├── telegram_bot/              # Telegram Bot
│   ├── client/                # Backend API client
│   ├── handlers/              # Bot handlers
│   └── main.py
│
├── alembic/                   # Database migrations
│   ├── env.py                 # ✅ Обновлен
│   └── versions/              # ✅ Обновлены
│
└── docker-compose.yml
```

---

## 🎯 Преимущества новой структуры

### 1. Логичная организация
- Всё относящееся к Backend в одной папке
- Database models логически часть Backend
- Проще понять структуру проекта

### 2. Независимость
- Backend полностью самодостаточен
- Можно вынести в отдельный репозиторий
- Telegram Bot не зависит от db моделей

### 3. Чистая архитектура
- Backend использует ORM модели (SQLAlchemy)
- Telegram Bot использует API клиент (словари/JSON)
- Четкое разделение слоев

### 4. Масштабируемость
- Легко добавить новые модели БД
- Можно добавить другие источники данных
- Готово к микросервисам

---

## 🔄 Импорты в разных частях проекта

### Backend код (использует ORM):
```python
# ORM модели базы данных
from backend.db.models.booking import BookingBase
from backend.db.models.user import UserBase

# Database session
from backend.db.database import SessionLocal

# Миграции
from backend.db.run_migrations import run_migrations
```

### Telegram Bot (использует API):
```python
# Бот НЕ импортирует db напрямую!
# Вместо этого использует API клиент:
from telegram_bot.client.backend_api import BackendAPIClient

# Пример:
api_client = BackendAPIClient()
booking = await api_client.get_booking(booking_id)  # Возвращает dict
```

### Alembic (миграции):
```python
# Импортирует модели для автоматической генерации миграций
from backend.db.models.base import Base
from backend.db.models.user import UserBase
from backend.db.models.booking import BookingBase
```

---

## 📝 Рекомендации

### Для разработки

1. **Новые модели БД создавать в:**
   ```
   backend/db/models/new_model.py
   ```

2. **После создания модели:**
   ```bash
   # Добавить импорт в alembic/env.py
   from backend.db.models.new_model import NewModelBase

   # Создать миграцию
   python -m alembic revision --autogenerate -m "add new_model"

   # Применить миграцию
   python -m alembic upgrade head
   ```

3. **Telegram Bot не должен:**
   - Импортировать из `backend.db.*`
   - Использовать ORM модели напрямую
   - Делать SQL запросы

   **Вместо этого:**
   - Использовать `BackendAPIClient`
   - Работать со словарями
   - Делать HTTP запросы к API

### Для тестирования

```python
# Backend тесты - можно использовать ORM
from backend.db.models.booking import BookingBase
from backend.db.database import SessionLocal

# Telegram Bot тесты - только API клиент
from telegram_bot.client.backend_api import BackendAPIClient
```

---

## ⚠️ Важные изменения для CI/CD

### Database миграции

**Старый путь:**
```bash
# Не работает больше
python -c "from db.run_migrations import run_migrations; run_migrations()"
```

**Новый путь:**
```bash
# Правильно
python -c "from backend.db.run_migrations import run_migrations; run_migrations()"

# Или через alembic напрямую
python -m alembic upgrade head
```

### Docker Compose

Если используется монтирование volumes, обновить пути:

**Было:**
```yaml
volumes:
  - ./db:/app/db
```

**Стало:**
```yaml
volumes:
  - ./backend/db:/app/backend/db
```

---

## ✅ Готово!

Папка `db/` успешно перенесена в `backend/db/`, все импорты обновлены, проверки пройдены.

**Проект готов к дальнейшей разработке с новой структурой! 🎉**

---

*Документ создан: 27 ноября 2025*
*Версия: 1.0*
