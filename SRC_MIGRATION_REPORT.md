# 🗂️ Отчет о миграции из папки src/

**Дата:** 27 ноября 2025

## ✅ Выполнено

### Удалена папка `src/`

Все содержимое папки `src/` было распределено между `backend/` и `telegram_bot/`, после чего папка `src/` была удалена.

---

## 📦 Что было перемещено

### В `telegram_bot/`:

| Из src/ | В telegram_bot/ | Статус |
|---------|----------------|--------|
| `src/constants.py` | `telegram_bot/constants.py` | ✅ |
| `src/helpers/` | `telegram_bot/helpers/` | ✅ |
| `src/handlers/` | `telegram_bot/handlers/` | ✅ Было ранее |
| `src/decorators/` | `telegram_bot/decorators/` | ✅ Было ранее |
| `src/date_time_picker/` | `telegram_bot/date_time_picker/` | ✅ Было ранее |

### В `backend/`:

| Из src/ | В backend/ | Статус |
|---------|------------|--------|
| `src/models/enum/` | `backend/models/enum/` | ✅ Было ранее |
| `src/services/` | `backend/services/` | ✅ Было ранее |
| `src/config/` | `backend/config/` | ✅ Было ранее |

---

## 🔧 Обновленные импорты

### Telegram Bot

**Было:**
```python
from src.constants import END, MENU
from src.helpers import string_helper
from src.decorators.callback_error_handler import safe_callback_query
from src.services.logger_service import LoggerService
```

**Стало:**
```python
from telegram_bot.constants import END, MENU
from telegram_bot.helpers import string_helper
from telegram_bot.decorators.callback_error_handler import safe_callback_query
from telegram_bot.services.logger_service import LoggerService
```

### Backend

**Было:**
```python
from src.models.enum.tariff import Tariff
from src.services.booking_service import BookingService
from src.services.logger_service import LoggerService
```

**Стало:**
```python
from backend.models.enum.tariff import Tariff
from backend.services.booking_service import BookingService
from backend.services.logger_service import LoggerService
```

---

## 📊 Статистика изменений

### Обновленные файлы

**Telegram Bot:** 24 файла
- handlers/: 13 файлов
- helpers/: 5 файлов
- services/redis/: 3 файла
- date_time_picker/: 2 файла
- decorators/: 1 файл

**Backend:** ~20 файлов
- api/v1/routers/: 6 файлов
- models/: 4 файла
- config/: 1 файл
- services/: ~9 файлов

### Импорты заменено

- `from src.*` → `from telegram_bot.*`: ~50+ мест
- `from src.*` → `from backend.*`: ~30+ мест

---

## ✅ Проверки пройдены

### Синтаксис
```bash
✅ telegram_bot/main.py - OK
✅ backend/main.py - OK
```

### Импорты
```bash
✅ Нет оставшихся импортов из src в telegram_bot
✅ Нет оставшихся импортов из src в backend
```

### Структура
```bash
✅ Папка src/ удалена
✅ Бэкап создан: src_backup_20251127_*.tar.gz
```

---

## 📁 Итоговая структура проекта

```
secret-house-booking-bot/
├── backend/                    # Backend API (FastAPI)
│   ├── api/v1/routers/        # REST endpoints
│   ├── config/                # Configuration
│   ├── models/                # Pydantic models
│   │   ├── enum/             # 📌 Из src/models/enum/
│   │   └── ...
│   ├── services/              # 📌 Из src/services/
│   └── main.py
│
├── telegram_bot/              # Telegram Bot
│   ├── client/                # Backend API client
│   ├── config/                # Bot configuration
│   ├── decorators/            # 📌 Было в src/
│   ├── handlers/              # 📌 Было в src/
│   ├── helpers/               # 📌 Из src/helpers/
│   ├── services/              # Bot-specific services
│   ├── constants.py           # 📌 Из src/constants.py
│   └── main.py
│
├── db/                        # Database models (SQLAlchemy)
├── alembic/                   # Database migrations
├── docker-compose.yml
└── requirements.txt
```

---

## 🔄 Откат (если понадобится)

Если нужно вернуть папку `src/`:

```bash
# Восстановить из бэкапа
tar -xzf src_backup_20251127_*.tar.gz

# Откатить импорты (автоматически не получится, нужно вручную)
# Или использовать git:
git checkout <previous-commit> -- src/
```

**Но откат НЕ рекомендуется** - новая структура более правильная!

---

## 🎯 Преимущества новой структуры

### 1. Четкое разделение
- `backend/` - только Backend API код
- `telegram_bot/` - только Telegram Bot код
- Нет общей "свалки" в `src/`

### 2. Независимость
- Backend и Bot - независимые модули
- Можно развивать отдельно
- Проще тестировать

### 3. Понятность
- Сразу ясно, где что находится
- Импорты явно показывают принадлежность
- Легче навигация по проекту

### 4. Масштабируемость
- Легко добавить новые сервисы
- Можно вынести в отдельные репозитории
- Готовность к монорепо структуре

---

## 📝 Рекомендации

### Для разработки

1. **Импорты в Telegram Bot:**
   ```python
   from telegram_bot.helpers import string_helper
   from telegram_bot.constants import END
   ```

2. **Импорты в Backend:**
   ```python
   from backend.services.booking_service import BookingService
   from backend.models.enum.tariff import Tariff
   ```

3. **Общие модели базы данных:**
   ```python
   from db.models.booking import BookingBase
   ```

### Для добавления новых файлов

**Telegram Bot специфичный код:**
- Хэндлеры → `telegram_bot/handlers/`
- Хелперы → `telegram_bot/helpers/`
- Декораторы → `telegram_bot/decorators/`

**Backend специфичный код:**
- API endpoints → `backend/api/v1/routers/`
- Бизнес-логика → `backend/services/`
- Модели → `backend/models/`

**Общий код:**
- Database models → `db/models/`
- Миграции → `alembic/versions/`

---

## ✅ Готово!

Папка `src/` успешно удалена, все файлы перемещены в правильные места, импорты обновлены, проверки пройдены.

**Проект готов к дальнейшей разработке с новой структурой! 🎉**

---

*Документ создан: 27 ноября 2025*
*Версия: 1.0*
