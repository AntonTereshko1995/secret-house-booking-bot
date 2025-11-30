# Testing Setup Complete ✅

Полная инфраструктура тестирования успешно настроена для проекта Secret House Booking Bot.

## 📦 Что было добавлено

### 1. Зависимости для тестирования
Обновлен [requirements.txt](requirements.txt):
- `pytest` - фреймворк тестирования
- `pytest-asyncio` - поддержка асинхронных тестов
- `pytest-mock` - мокирование зависимостей
- `pytest-cov` - отчеты о покрытии кода
- `freezegun` - мокирование времени/даты
- `faker` - генерация тестовых данных

### 2. Конфигурация pytest
- **[pytest.ini](pytest.ini)** - настройки pytest с маркерами тестов
- **[tests/conftest.py](tests/conftest.py)** - общие фикстуры и настройки

### 3. Тесты

#### Unit тесты (быстрые, без внешних зависимостей):
- ✅ [tests/test_string_helper.py](tests/test_string_helper.py) - 40+ тестов для строковых функций
- ✅ [tests/test_date_time_helper.py](tests/test_date_time_helper.py) - 30+ тестов для работы с датой/временем
- ✅ [tests/test_calculation_rate_service.py](tests/test_calculation_rate_service.py) - тесты расчета стоимости
- ✅ [tests/test_models_enums.py](tests/test_models_enums.py) - тесты для enum моделей

#### Integration тесты:
- ✅ [tests/test_redis_integration.py](tests/test_redis_integration.py) - тесты Redis сервиса
- ✅ [tests/test_calculation_rate_integration.py](tests/test_calculation_rate_integration.py) - интеграционные тесты расчета
- ✅ [tests/test_date_pricing_service.py](tests/test_date_pricing_service.py) - тесты ценообразования по датам
- ✅ [tests/test_chat_id_management.py](tests/test_chat_id_management.py) - управление chat ID
- ✅ [tests/test_chat_id_fix.py](tests/test_chat_id_fix.py) - фиксы chat ID

### 4. VS Code интеграция

#### Файлы конфигурации:
- **[.vscode/settings.json](.vscode/settings.json)** - автоматическое обнаружение тестов
- **[.vscode/launch.json](.vscode/launch.json)** - 4 конфигурации для отладки тестов
- **[.vscode/tasks.json](.vscode/tasks.json)** - 7 задач для быстрого запуска
- **[.vscode/extensions.json](.vscode/extensions.json)** - рекомендуемые расширения
- **[.vscode/README.md](.vscode/README.md)** - подробная документация

#### Доступные конфигурации запуска:
1. 🧪 Run All Tests - все тесты
2. 🧪 Run Unit Tests - только unit тесты
3. 🧪 Run Tests with Coverage - с отчетом покрытия
4. 🧪 Debug Current Test File - отладка текущего файла

#### Доступные задачи (Tasks):
1. Run All Tests (по умолчанию: `Cmd+Shift+B`)
2. Run Unit Tests
3. Run Integration Tests
4. Run Tests with Coverage
5. Run Fast Tests
6. Open Coverage Report
7. Clean Test Artifacts

### 5. Документация
- **[tests/README.md](tests/README.md)** - полное руководство по тестированию
- **[.vscode/README.md](.vscode/README.md)** - руководство по VS Code
- **[CLAUDE.md](CLAUDE.md)** - обновлено с секцией Testing
- **[Makefile](Makefile)** - удобные команды make для тестирования

### 6. Общие фикстуры (tests/conftest.py)

#### Фикстуры для тестовых данных:
- `test_date` - стандартная тестовая дата
- `test_datetime` - стандартная datetime
- `sample_rental_price` - пример тарифа
- `sample_date_pricing_rules` - правила ценообразования
- `sample_booking_data` - данные бронирования
- `sample_gift_certificate_data` - данные сертификата

#### Mock фикстуры:
- `mock_telegram_update` - мок Telegram Update
- `mock_telegram_context` - мок Telegram Context
- `mock_file_service` - мок FileService
- `mock_redis_service` - мок Redis
- `mock_database_service` - мок Database
- `mock_calendar_service` - мок Google Calendar
- `mock_gpt_service` - мок OpenAI GPT
- `mock_settings_service` - мок Settings

## 🚀 Быстрый старт

### Установка зависимостей
```bash
pip install -r requirements.txt
```

### Запуск тестов

#### Командная строка:
```bash
# Все тесты
pytest

# Unit тесты (быстрые)
pytest -m unit

# С покрытием кода
pytest --cov=src --cov-report=html

# Используя Makefile
make test
make test-unit
make test-cov
```

#### VS Code:
1. **Testing Panel**: `Cmd+Shift+T` → кликнуть на play
2. **Debug Panel**: `Cmd+Shift+D` → выбрать конфигурацию → `F5`
3. **Quick Task**: `Cmd+Shift+B` (запустит все тесты)

## 📊 Маркеры тестов

```python
@pytest.mark.unit              # Быстрые unit тесты
@pytest.mark.integration       # Интеграционные тесты
@pytest.mark.slow              # Медленные тесты
@pytest.mark.requires_db       # Требуют базу данных
@pytest.mark.requires_redis    # Требуют Redis
@pytest.mark.requires_external # Требуют внешние API
```

### Запуск по маркерам:
```bash
pytest -m unit                    # Только unit
pytest -m integration             # Только integration
pytest -m "unit and not slow"     # Быстрые unit
pytest -m "not requires_external" # Без внешних зависимостей
```

## 📈 Покрытие кода

### Запуск с покрытием:
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Цели покрытия:
- **Общее**: 80%+
- **Критичные пути** (booking workflow): 100%
- **Helpers**: 90%+
- **Services**: 80%+

## 🔧 VS Code функционал

### Testing Panel (Cmd+Shift+T):
- ✅ Автоматическое обнаружение тестов при сохранении
- ✅ Запуск отдельных тестов одним кликом
- ✅ Зеленые/красные индикаторы статуса
- ✅ Просмотр результатов inline

### Debug configurations:
- ✅ Точки останова (breakpoints) в тестах
- ✅ Пошаговая отладка (F10/F11)
- ✅ Инспекция переменных
- ✅ Debug console

### Tasks (Cmd+Shift+P → "Tasks: Run Task"):
- ✅ Быстрый запуск без настройки
- ✅ Вывод в отдельный терминал
- ✅ Автоматические команды make

## 📝 Примеры написания тестов

### Простой unit тест:
```python
import pytest

@pytest.mark.unit
class TestMyFunction:
    def test_basic_case(self):
        result = my_function("input")
        assert result == "expected"
```

### С использованием фикстур:
```python
@pytest.mark.unit
def test_with_fixture(sample_rental_price):
    assert sample_rental_price.price == 700
    assert sample_rental_price.sauna_price == 100
```

### Интеграционный тест:
```python
@pytest.mark.integration
@pytest.mark.requires_redis
class TestRedisIntegration:
    def test_redis_set_get(self, mock_redis_client):
        # тест с Redis
        pass
```

### Асинхронный тест:
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

## 🎯 Best Practices

1. **Изоляция тестов**: каждый тест независим
2. **Описательные имена**: `test_booking_calculation_with_sauna`
3. **Мокирование**: не вызывать реальные API в unit тестах
4. **Граничные случаи**: тестировать edge cases
5. **Быстрые тесты**: unit тесты < 100ms
6. **Фикстуры**: переиспользовать общие данные
7. **Маркеры**: правильно категоризировать тесты

## 🔍 Troubleshooting

### Тесты не обнаруживаются в VS Code:
1. Проверить Python interpreter
2. Обновить Testing Panel (кнопка refresh)
3. Проверить Output → Python Test Log

### Ошибки импорта:
1. Проверить `sys.path` в тестах
2. Убедиться что запуск из корня проекта
3. Проверить `python.analysis.extraPaths` в settings.json

### Slow performance:
```bash
# Запуск параллельно
pip install pytest-xdist
pytest -n auto
```

## 📚 Дополнительные ресурсы

- [Pytest Documentation](https://docs.pytest.org/)
- [VS Code Python Testing](https://code.visualstudio.com/docs/python/testing)
- [tests/README.md](tests/README.md) - подробное руководство
- [.vscode/README.md](.vscode/README.md) - VS Code интеграция

## ✨ Следующие шаги

1. Запустите тесты: `pytest` или `make test`
2. Проверьте покрытие: `make test-cov`
3. Откройте VS Code Testing Panel: `Cmd+Shift+T`
4. Попробуйте отладку теста с breakpoint
5. Добавьте новые тесты для своего кода

---

**Готово к использованию!** 🎉

Все инструменты настроены и готовы к работе. Просто запустите `pytest` или используйте VS Code Testing Panel.
