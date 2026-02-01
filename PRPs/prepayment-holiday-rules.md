name: "Изменение правил предоплаты с учетом праздничных дней"
description: |

## Цель
Реализовать новую систему расчета предоплаты для бронирования дома с учетом обычных и праздничных дней:
- **Обычные дни**: предоплата 50% от общей стоимости бронирования
- **Праздничные дни**: предоплата 100% от стоимости бронирования

## Почему
- **Бизнес-ценность**: Снижение финансовых рисков на праздничные даты (высокий спрос)
- **Гибкость**: Автоматический расчет предоплаты без ручного вмешательства администратора
- **Прозрачность**: Клиент сразу видит правильную сумму предоплаты при бронировании
- **Интеграция**: Использует существующую архитектуру date-based правил

## Что
Система автоматического расчета предоплаты, которая:
1. Проверяет, попадает ли дата бронирования на праздничный день
2. Рассчитывает предоплату как 50% или 100% от общей стоимости
3. Отображает правильную сумму предоплаты в сообщениях бота
4. Сохраняет рассчитанную сумму в базе данных при создании бронирования

### Критерии успеха
- [ ] Предоплата рассчитывается как 50% для обычных дней
- [ ] Предоплата рассчитывается как 100% для праздничных дней
- [ ] Список праздников загружается из конфигурационного файла
- [ ] Сообщения бота показывают правильную сумму предоплаты
- [ ] База данных сохраняет рассчитанную предоплату
- [ ] Администратор может вручную изменить предоплату при необходимости
- [ ] Все существующие тесты проходят успешно

## Весь необходимый контекст

### Документация и ссылки
```yaml
# ОБЯЗАТЕЛЬНО К ПРОЧТЕНИЮ - Включите в контекст

- file: src/services/date_pricing_service.py
  why: Существующий паттерн для date-based правил - нужно скопировать архитектуру
  pattern: Singleton service с загрузкой правил из JSON

- file: src/models/date_pricing_rule.py
  why: Модель для date-based правил - создадим аналогичную для предоплаты
  pattern: Dataclass с валидацией, методы applies_to_date()

- file: src/services/file_service.py
  why: Сервис загрузки конфигураций из JSON - добавим метод для загрузки правил предоплаты
  pattern: Singleton с методами get_*_rules()

- file: src/config/date_pricing_rules.json
  why: Пример конфигурационного файла - создадим похожий для праздников
  structure: JSON с массивом правил

- file: db/models/booking.py
  why: Модель бронирования с полем prepayment_price (строка 35-37)
  critical: Поле уже существует, нужно только правильно рассчитывать значение

- file: src/handlers/booking_handler.py
  why: Обработчик бронирования, где отображается предоплата (строка 1011)
  critical: Заменить константу PREPAYMENT на динамический расчет

- file: src/config/config.py
  why: Содержит константу PREPAYMENT = 80 (строка 13)
  note: Константа останется как fallback, но не будет использоваться напрямую

- file: src/services/database/booking_repository.py
  why: Репозиторий для работы с бронированиями (строки 470-474)
  pattern: Метод update_booking с параметром prepayment_price

- url: https://docs.python.org/3/library/datetime.html
  why: Работа с датами для проверки праздников
  section: datetime.date, date ranges

- url: https://python-telegram-bot.readthedocs.io/
  why: Документация по python-telegram-bot для обработчиков
  critical: Async/await patterns в handlers
```

### Текущее дерево кодовой базы
```bash
secret-house-booking-bot/
├── src/
│   ├── config/
│   │   ├── config.py                          # PREPAYMENT = 80 константа
│   │   ├── date_pricing_rules.json            # Пример date-based правил
│   │   ├── tariff_rate.json                   # Тарифы
│   │   └── .env.debug                         # Environment переменные
│   ├── handlers/
│   │   ├── booking_handler.py                 # MODIFY: динамический расчет предоплаты
│   │   ├── admin_handler.py                   # Может потребовать обновление
│   │   └── booking_details_handler.py         # Отображение деталей бронирования
│   ├── models/
│   │   ├── date_pricing_rule.py               # REFERENCE: паттерн для копирования
│   │   └── booking_draft.py                   # Draft модель для Redis
│   ├── services/
│   │   ├── date_pricing_service.py            # REFERENCE: архитектура сервиса
│   │   ├── calculation_rate_service.py        # Расчет стоимости бронирования
│   │   ├── file_service.py                    # MODIFY: добавить метод загрузки правил
│   │   ├── database_service.py                # Фасад для работы с БД
│   │   └── database/
│   │       └── booking_repository.py          # CRUD для бронирований
│   ├── helpers/
│   │   └── string_helper.py                   # Форматирование сообщений
│   └── main.py                                # Entry point
├── db/
│   └── models/
│       └── booking.py                         # Модель BookingBase с prepayment_price
├── alembic/                                   # Миграции БД
├── tests/                                     # Тесты (пустая директория)
├── requirements.txt                           # Зависимости Python
└── PRPs/                                      # Документация PRP

```

### Желаемое дерево кодовой базы с новыми файлами
```bash
secret-house-booking-bot/
├── src/
│   ├── config/
│   │   └── holiday_prepayment_rules.json      # NEW: Правила предоплаты для праздников
│   ├── models/
│   │   └── holiday_prepayment_rule.py         # NEW: Модель правила предоплаты
│   └── services/
│       └── prepayment_service.py              # NEW: Сервис расчета предоплаты
```

### Известные особенности кодовой базы и библиотек
```python
# КРИТИЧНО: Python-telegram-bot требует async/await во всех handlers
# Все функции обработчиков должны быть async

# КРИТИЧНО: Singleton decorator используется для сервисов
# from singleton_decorator import singleton
# @singleton перед классом

# КРИТИЧНО: SQLAlchemy ORM с Mapped типами
# Модели используют Mapped[type] = mapped_column(...)

# КРИТИЧНО: dataclasses_json для JSON сериализации
# @dataclass_json и @dataclass для моделей

# КРИТИЧНО: Redis используется для хранения draft бронирований
# Финальное бронирование сохраняется в SQLite через BookingBase

# КРИТИЧНО: CalculationRateService уже считает полную стоимость бронирования
# Предоплата должна быть % от этой стоимости

# ВАЖНО: DatePricingService использует applies_to_date(target_date: date)
# Скопируем этот паттерн для HolidayPrepaymentService

# ВАЖНО: FileService загружает JSON с валидацией через Pydantic/dataclasses
# Следуем этому паттерну

# ВАЖНО: Константа PREPAYMENT = 80 используется как fallback
# Не удаляем её, но перестаем использовать напрямую

# ВАЖНО: Администратор может вручную изменить предоплату через админ-панель
# Новая логика не должна ломать эту функциональность
```

### Список праздников Беларуси (из требований)
```python
HOLIDAYS = {
    # Новый год (31 декабря - 2 января)
    "new_year": {
        "dates": ["12-31", "01-01", "01-02"],  # MM-DD формат
        "recurring": True,  # Каждый год
        "name": "Новый год"
    },
    # Рождество Христово (7 января)
    "christmas_orthodox": {
        "dates": ["01-07"],
        "recurring": True,
        "name": "Рождество Христово (православное)"
    },
    # День всех влюбленных (14 февраля)
    "valentines_day": {
        "dates": ["02-14"],
        "recurring": True,
        "name": "День всех влюбленных"
    },
    # День защитников Отечества (23 февраля)
    "defenders_day": {
        "dates": ["02-23"],
        "recurring": True,
        "name": "День защитников Отечества"
    },
    # Международный женский день (8 марта)
    "womens_day": {
        "dates": ["03-08"],
        "recurring": True,
        "name": "Международный женский день"
    },
    # Радуница (21 апреля) - ВАЖНО: дата меняется каждый год!
    "radonitsa": {
        "dates": ["04-21"],  # 2026 год, нужно обновлять ежегодно
        "recurring": False,
        "name": "Радуница"
    },
    # Праздник труда (1 мая)
    "labor_day": {
        "dates": ["05-01"],
        "recurring": True,
        "name": "Праздник труда"
    },
    # День Победы (9 мая)
    "victory_day": {
        "dates": ["05-09"],
        "recurring": True,
        "name": "День Победы"
    },
    # День Независимости РБ (3 июля)
    "independence_day": {
        "dates": ["07-03"],
        "recurring": True,
        "name": "День Независимости Республики Беларусь"
    },
    # День Октябрьской революции (7 ноября)
    "october_revolution": {
        "dates": ["11-07"],
        "recurring": True,
        "name": "День Октябрьской революции"
    },
    # Рождество Христово католическое (25 декабря)
    "christmas_catholic": {
        "dates": ["12-25"],
        "recurring": True,
        "name": "Рождество Христово (католическое)"
    }
}
```

## План реализации

### Модели данных и структура

Создадим модель правила предоплаты по аналогии с DatePricingRule:

```python
# src/models/holiday_prepayment_rule.py

@dataclass_json
@dataclass
class HolidayPrepaymentRule:
    """Правило предоплаты для праздничного дня."""

    rule_id: str  # Уникальный идентификатор (например, "new_year_2026")
    date: str  # Конкретная дата в формате "YYYY-MM-DD" или "MM-DD" для повторяющихся
    is_recurring: bool  # True если праздник повторяется каждый год
    prepayment_percentage: int  # Процент предоплаты (обычно 100 для праздников)
    name: str  # Название праздника
    is_active: bool = True  # Можно отключить правило
    description: Optional[str] = None  # Дополнительное описание

    def __post_init__(self):
        """Валидация после инициализации."""
        # Валидация формата даты
        if self.is_recurring:
            # Для повторяющихся: MM-DD
            if not re.match(r'^\d{2}-\d{2}$', self.date):
                raise ValueError(f"Recurring date must be in MM-DD format: {self.date}")
        else:
            # Для разовых: YYYY-MM-DD
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', self.date):
                raise ValueError(f"Non-recurring date must be in YYYY-MM-DD format: {self.date}")

        # Валидация процента
        if not 0 <= self.prepayment_percentage <= 100:
            raise ValueError(f"Prepayment percentage must be 0-100: {self.prepayment_percentage}")

    def applies_to_date(self, target_date: date) -> bool:
        """Проверяет, применяется ли правило к указанной дате."""
        if not self.is_active:
            return False

        if self.is_recurring:
            # Проверяем только месяц и день
            date_str = target_date.strftime("%m-%d")
            return date_str == self.date
        else:
            # Проверяем полную дату
            target_str = target_date.strftime("%Y-%m-%d")
            return target_str == self.date
```

### Список задач для выполнения PRP в порядке реализации

```yaml
Задача 1: Создать модель HolidayPrepaymentRule
СОЗДАТЬ src/models/holiday_prepayment_rule.py:
  - СКОПИРОВАТЬ структуру из date_pricing_rule.py
  - ИЗМЕНИТЬ поля под нужды предоплаты (prepayment_percentage)
  - ДОБАВИТЬ поле is_recurring для повторяющихся праздников
  - РЕАЛИЗОВАТЬ метод applies_to_date(target_date: date) -> bool
  - ДОБАВИТЬ валидацию в __post_init__
  - СОХРАНИТЬ паттерн @dataclass_json и @dataclass

Задача 2: Создать конфигурационный файл с праздниками
СОЗДАТЬ src/config/holiday_prepayment_rules.json:
  - ФОРМАТ: JSON с массивом "prepayment_rules"
  - ДОБАВИТЬ все праздники из списка выше
  - ДЛЯ повторяющихся праздников: "date": "MM-DD", "is_recurring": true
  - ДЛЯ разовых (Радуница): "date": "YYYY-MM-DD", "is_recurring": false
  - ВСЕ праздники: "prepayment_percentage": 100, "is_active": true
  - ПРИМЕР структуры:
    ```json
    {
      "prepayment_rules": [
        {
          "rule_id": "new_year",
          "date": "01-01",
          "is_recurring": true,
          "prepayment_percentage": 100,
          "name": "Новый год",
          "is_active": true,
          "description": "100% предоплата на Новый год"
        }
      ]
    }
    ```

Задача 3: Обновить FileService для загрузки правил предоплаты
ИЗМЕНИТЬ src/services/file_service.py:
  - НАЙТИ: класс FileService (строка 12)
  - ДОБАВИТЬ константу: _HOLIDAY_PREPAYMENT_RULES_JSON = "src/config/holiday_prepayment_rules.json"
  - ДОБАВИТЬ import: from src.models.holiday_prepayment_rule import HolidayPrepaymentRule
  - СКОПИРОВАТЬ метод get_date_pricing_rules() (строки 56-66)
  - СОЗДАТЬ новый метод:
    ```python
    def get_holiday_prepayment_rules(self) -> List[HolidayPrepaymentRule]:
        if not os.path.exists(self._HOLIDAY_PREPAYMENT_RULES_JSON):
            raise FileNotFoundError(
                f"Файл {self._HOLIDAY_PREPAYMENT_RULES_JSON} не существует."
            )

        rules_list = []
        with open(self._HOLIDAY_PREPAYMENT_RULES_JSON, "r", encoding="utf-8") as file:
            data = json.load(file)
            rules_list = [HolidayPrepaymentRule(**item) for item in data["prepayment_rules"]]
        return rules_list
    ```

Задача 4: Создать PrepaymentService для расчета предоплаты
СОЗДАТЬ src/services/prepayment_service.py:
  - СКОПИРОВАТЬ архитектуру из date_pricing_service.py
  - ИСПОЛЬЗОВАТЬ @singleton декоратор
  - РЕАЛИЗОВАТЬ методы:
    * get_applicable_rules(target_date: date) -> List[HolidayPrepaymentRule]
    * get_effective_rule(target_date: date) -> Optional[HolidayPrepaymentRule]
    * is_holiday(target_date: date) -> bool
    * calculate_prepayment(total_price: float, booking_date: date) -> float
  - ПАТТЕРН _try_load_rules() для ленивой загрузки правил
  - ЛОГИКА calculate_prepayment:
    ```python
    def calculate_prepayment(self, total_price: float, booking_date: date) -> float:
        """
        Рассчитывает предоплату на основе общей стоимости и даты бронирования.

        Возвращает:
        - 100% от стоимости для праздничных дней
        - 50% от стоимости для обычных дней
        """
        effective_rule = self.get_effective_rule(booking_date)

        if effective_rule:
            # Праздничный день - применяем процент из правила (обычно 100%)
            percentage = effective_rule.prepayment_percentage
            prepayment = total_price * (percentage / 100.0)
            return round(prepayment, 2)
        else:
            # Обычный день - 50% предоплата
            return round(total_price * 0.5, 2)
    ```

Задача 5: Обновить booking_handler.py для динамического расчета
ИЗМЕНИТЬ src/handlers/booking_handler.py:
  - НАЙТИ: строку 1011 с f"🔹 <b>Предоплата:</b> {PREPAYMENT} руб.\n"
  - ДОБАВИТЬ import:
    ```python
    from src.services.prepayment_service import PrepaymentService
    ```
  - ИЗМЕНИТЬ функцию payment_message() (около строки 980):
    ```python
    # Получаем бронирование из Redis
    booking = redis_service.get_booking(update)

    # НОВОЕ: рассчитываем предоплату динамически
    prepayment_service = PrepaymentService()
    prepayment_amount = prepayment_service.calculate_prepayment(
        total_price=booking.price,
        booking_date=booking.start_booking_date.date()
    )

    # Сохраняем рассчитанную предоплату в Redis draft
    redis_service.update_booking_field(update, "prepayment_price", prepayment_amount)

    # ЗАМЕНИТЬ строку 1011:
    message = (
        f"💰 <b>Общая сумма оплаты:</b> {booking.price} руб.\n\n"
        f"🔹 <b>Предоплата:</b> {prepayment_amount} руб.\n"  # ИЗМЕНЕНО
        "💡 Предоплата не возвращается при отмене бронирования..."
    )
    ```
  - ВАЖНО: не трогать блок для подарочных сертификатов (строка 999-1007)

Задача 6: Обновить сохранение бронирования в БД
ИЗМЕНИТЬ src/handlers/booking_handler.py:
  - НАЙТИ: функцию, которая вызывает database_service.create_booking()
  - НАЙТИ все места где создается BookingBase
  - УБЕДИТЬСЯ что prepayment_price передается из Redis draft:
    ```python
    booking = redis_service.get_booking(update)

    # При создании бронирования передаем рассчитанную предоплату
    new_booking = database_service.create_booking(
        user_id=user.id,
        start_date=booking.start_booking_date,
        end_date=booking.finish_booking_date,
        tariff=booking.tariff,
        price=booking.price,
        prepayment_price=booking.prepayment_price,  # ДОБАВИТЬ если отсутствует
        # ... остальные поля
    )
    ```

Задача 7: Обновить модель BookingDraft в Redis
ПРОВЕРИТЬ src/models/booking_draft.py:
  - УБЕДИТЬСЯ что есть поле prepayment_price: Optional[float]
  - ЕСЛИ отсутствует - ДОБАВИТЬ:
    ```python
    @dataclass
    class BookingDraft:
        # ... существующие поля
        prepayment_price: Optional[float] = None  # НОВОЕ если нет
    ```

Задача 8: Обновить отображение в admin_handler
ПРОВЕРИТЬ src/handlers/admin_handler.py:
  - НАЙТИ строку 1025 с f"Текущая предоплата: <b>{booking.prepayment_price}"
  - ПРОВЕРИТЬ что отображается booking.prepayment_price (из БД), а не константа
  - НЕ МЕНЯТЬ логику ручного изменения предоплаты администратором

Задача 9: Добавить вспомогательные методы (опционально)
РАССМОТРЕТЬ добавление в PrepaymentService:
  - get_holiday_name(target_date: date) -> Optional[str] - для отображения названия праздника
  - get_prepayment_explanation(target_date: date) -> str - текст объяснения для пользователя
  - ПРИМЕР:
    ```python
    def get_prepayment_explanation(self, target_date: date) -> str:
        """Возвращает текст объяснения размера предоплаты."""
        rule = self.get_effective_rule(target_date)
        if rule:
            return f"🎉 {rule.name} - требуется полная предоплата (100%)"
        else:
            return "Стандартная предоплата составляет 50% от стоимости"
    ```

Задача 10: Добавить логирование
ДОБАВИТЬ в PrepaymentService:
  - Import: from src.services.logger_service import LoggerService
  - ЛОГИРОВАТЬ расчеты предоплаты:
    ```python
    def calculate_prepayment(self, total_price: float, booking_date: date) -> float:
        effective_rule = self.get_effective_rule(booking_date)

        if effective_rule:
            LoggerService.info(
                __name__,
                f"Holiday prepayment: {effective_rule.name} on {booking_date}, "
                f"{effective_rule.prepayment_percentage}% = {prepayment}"
            )
        else:
            LoggerService.info(
                __name__,
                f"Standard prepayment: {booking_date}, 50% = {prepayment}"
            )

        return prepayment
    ```
```

### Псевдокод для каждой задачи (критические детали)

```python
# Задача 4: PrepaymentService - ключевая логика

@singleton
class PrepaymentService:
    """Сервис для расчета предоплаты с учетом праздничных дней."""

    _rules: List[HolidayPrepaymentRule] = []

    def get_applicable_rules(self, target_date: date) -> List[HolidayPrepaymentRule]:
        """Получить все активные правила для указанной даты."""
        rules = self._try_load_rules()
        applicable = []

        for rule in rules:
            if rule.applies_to_date(target_date):
                applicable.append(rule)

        return applicable

    def get_effective_rule(self, target_date: date) -> Optional[HolidayPrepaymentRule]:
        """
        Получить правило с наивысшим приоритетом для указанной даты.
        Если несколько правил применяются - берем первое (по rule_id).
        """
        applicable_rules = self.get_applicable_rules(target_date)
        return applicable_rules[0] if applicable_rules else None

    def is_holiday(self, target_date: date) -> bool:
        """Проверить, является ли дата праздничной."""
        return self.get_effective_rule(target_date) is not None

    def calculate_prepayment(
        self,
        total_price: float,
        booking_date: date
    ) -> float:
        """
        Рассчитывает предоплату на основе стоимости и даты.

        ПАТТЕРН: Проверяем правила -> применяем процент -> округляем

        Args:
            total_price: Полная стоимость бронирования
            booking_date: Дата начала бронирования

        Returns:
            Сумма предоплаты в рублях
        """
        effective_rule = self.get_effective_rule(booking_date)

        if effective_rule:
            # ПРАЗДНИЧНЫЙ ДЕНЬ: применяем процент из правила
            percentage = effective_rule.prepayment_percentage
            prepayment = total_price * (percentage / 100.0)

            LoggerService.info(
                __name__,
                f"Holiday prepayment calculation: {effective_rule.name}, "
                f"{percentage}% of {total_price} = {prepayment}"
            )
        else:
            # ОБЫЧНЫЙ ДЕНЬ: 50% предоплата
            prepayment = total_price * 0.5

            LoggerService.info(
                __name__,
                f"Standard prepayment calculation: 50% of {total_price} = {prepayment}"
            )

        # КРИТИЧНО: округляем до 2 знаков после запятой
        return round(prepayment, 2)

    def get_holiday_name(self, target_date: date) -> Optional[str]:
        """Получить название праздника для указанной даты (если есть)."""
        rule = self.get_effective_rule(target_date)
        return rule.name if rule else None

    def _try_load_rules(self) -> List[HolidayPrepaymentRule]:
        """
        Ленивая загрузка правил предоплаты.
        ПАТТЕРН: Singleton + lazy loading (как в DatePricingService)
        """
        if not self._rules:
            file_service = FileService()
            self._rules = file_service.get_holiday_prepayment_rules()
        return self._rules


# Задача 5: Обновление booking_handler.py

async def payment_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение сообщения с информацией об оплате.
    КРИТИЧНО: Рассчитываем предоплату динамически перед отображением.
    """
    LoggerService.info(__name__, "Payment message", update)

    # Получаем draft бронирования из Redis
    booking = redis_service.get_booking(update)

    # НОВАЯ ЛОГИКА: Расчет предоплаты
    prepayment_service = PrepaymentService()
    prepayment_amount = prepayment_service.calculate_prepayment(
        total_price=booking.price,
        booking_date=booking.start_booking_date.date()
    )

    # Сохраняем в Redis draft для последующего использования
    redis_service.update_booking_field(
        update,
        "prepayment_price",
        prepayment_amount
    )

    # КРИТИЧНО: Проверяем тип тарифа (подарочный сертификат - особый случай)
    if booking.tariff == Tariff.GIFT:
        # Подарочный сертификат: 100% предоплата всегда
        message = (
            f"💰 <b>Общая сумма оплаты:</b> {booking.price} руб.\n\n"
            f"🔹 <b>Предоплата:</b> {booking.price} руб.\n"  # 100% для подарка
            "📌 <b>Доступные способы оплаты (BSB-Bank):</b>\n"
            # ... rest of gift certificate message
        )
    else:
        # Обычное бронирование: используем рассчитанную предоплату

        # ОПЦИОНАЛЬНО: добавляем объяснение если праздник
        holiday_explanation = ""
        if prepayment_service.is_holiday(booking.start_booking_date.date()):
            holiday_name = prepayment_service.get_holiday_name(
                booking.start_booking_date.date()
            )
            holiday_explanation = f"\n🎉 <b>{holiday_name}</b> - требуется полная предоплата.\n"

        message = (
            f"💰 <b>Общая сумма оплаты:</b> {booking.price} руб.\n\n"
            f"🔹 <b>Предоплата:</b> {prepayment_amount} руб.\n"  # ИЗМЕНЕНО
            f"{holiday_explanation}"  # НОВОЕ
            "💡 Предоплата не возвращается при отмене бронирования, "
            "но вы можете перенести бронь на другую дату.\n\n"
            "📌 <b>Способы оплаты (BSB-Bank):</b>\n"
            f"💳 По номеру карты: <b>{BANK_CARD_NUMBER}</b>\n\n"
            "❗ <b>Важно!</b>\n"
            "После оплаты отправьте скриншот или PDF документ с чеком.\n"
            "📩 Это необходимо для подтверждения вашей предоплаты.\n\n"
            "🙏 Спасибо за понимание!"
        )

    # ... rest of handler (keyboard, reply_markup, etc.)
```

### Точки интеграции

```yaml
КОНФИГУРАЦИЯ:
  - create: src/config/holiday_prepayment_rules.json
  - pattern: JSON file с массивом правил
  - validation: Загружается через FileService, валидируется через dataclass

МОДЕЛИ ДАННЫХ:
  - create: src/models/holiday_prepayment_rule.py
  - integration: Используется в PrepaymentService
  - pattern: @dataclass + @dataclass_json + validation

СЕРВИСЫ:
  - create: src/services/prepayment_service.py
  - integration: Используется в booking_handler.py
  - pattern: @singleton + lazy loading правил

ФАЙЛОВЫЙ СЕРВИС:
  - modify: src/services/file_service.py
  - add: метод get_holiday_prepayment_rules()
  - pattern: Аналогично get_date_pricing_rules()

ОБРАБОТЧИКИ:
  - modify: src/handlers/booking_handler.py
  - location: функция payment_message() (строка ~980)
  - change: Заменить константу PREPAYMENT на динамический расчет

БАЗА ДАННЫХ:
  - no migration needed: поле prepayment_price уже существует
  - ensure: Значение передается при create_booking()

REDIS DRAFT:
  - ensure: BookingDraft имеет поле prepayment_price
  - save: Перед сохранением в БД предоплата уже рассчитана
```

## Цикл валидации

### Уровень 1: Синтаксис и стиль
```bash
# Запустить ИЗ корневой директории проекта
cd C:\projects\secret-house-booking-bot

# 1. Установить зависимости (если еще не установлены)
pip install -r requirements.txt

# 2. Проверка синтаксиса Python
python -m py_compile src/models/holiday_prepayment_rule.py
python -m py_compile src/services/prepayment_service.py
python -m py_compile src/services/file_service.py

# Ожидается: Нет ошибок компиляции
# Если есть ошибки: Исправить синтаксические ошибки, повторить
```

### Уровень 2: Валидация JSON конфигурации
```python
# Создать временный скрипт для проверки
# test_config_validation.py

import json
from src.models.holiday_prepayment_rule import HolidayPrepaymentRule

def test_load_rules():
    """Тестирует корректность загрузки правил из JSON."""
    with open("src/config/holiday_prepayment_rules.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    rules = [HolidayPrepaymentRule(**item) for item in data["prepayment_rules"]]

    print(f"✓ Загружено {len(rules)} правил")

    for rule in rules:
        print(f"  - {rule.name}: {rule.date} ({rule.prepayment_percentage}%)")

    return rules

if __name__ == "__main__":
    try:
        rules = test_load_rules()
        print("\n✓ Все правила успешно загружены и валидированы")
    except Exception as e:
        print(f"\n✗ Ошибка валидации: {e}")
        exit(1)
```

```bash
# Запустить тест валидации
python test_config_validation.py

# Ожидается: Все правила загружены без ошибок
# Если ошибки: Исправить JSON или модель, повторить
```

### Уровень 3: Интеграционное тестирование сервиса
```python
# test_prepayment_service.py

from datetime import date
from src.services.prepayment_service import PrepaymentService

def test_standard_day_prepayment():
    """Тест предоплаты для обычного дня (50%)."""
    service = PrepaymentService()

    # Тестовая дата: обычный день (не праздник)
    test_date = date(2026, 3, 15)  # 15 марта 2026
    total_price = 1000.0

    prepayment = service.calculate_prepayment(total_price, test_date)

    expected = 500.0  # 50% от 1000
    assert prepayment == expected, f"Expected {expected}, got {prepayment}"
    print(f"✓ Стандартная предоплата: {prepayment} руб. (50%)")

def test_holiday_prepayment():
    """Тест предоплаты для праздничного дня (100%)."""
    service = PrepaymentService()

    # Тестовая дата: Новый год
    test_date = date(2026, 1, 1)  # 1 января 2026
    total_price = 1000.0

    prepayment = service.calculate_prepayment(total_price, test_date)

    expected = 1000.0  # 100% от 1000
    assert prepayment == expected, f"Expected {expected}, got {prepayment}"
    print(f"✓ Праздничная предоплата: {prepayment} руб. (100%)")

    holiday_name = service.get_holiday_name(test_date)
    print(f"  Праздник: {holiday_name}")

def test_recurring_holiday():
    """Тест повторяющегося праздника (День Победы)."""
    service = PrepaymentService()

    # День Победы: 9 мая
    test_date = date(2026, 5, 9)
    total_price = 800.0

    prepayment = service.calculate_prepayment(total_price, test_date)

    assert service.is_holiday(test_date), "9 мая должен быть праздником"
    assert prepayment == 800.0, f"Expected 800.0, got {prepayment}"
    print(f"✓ День Победы: {prepayment} руб. (100%)")

def test_valentines_day():
    """Тест День всех влюбленных (14 февраля)."""
    service = PrepaymentService()

    test_date = date(2026, 2, 14)
    total_price = 600.0

    prepayment = service.calculate_prepayment(total_price, test_date)

    assert prepayment == 600.0
    print(f"✓ День всех влюбленных: {prepayment} руб. (100%)")

def test_rounding():
    """Тест округления предоплаты."""
    service = PrepaymentService()

    test_date = date(2026, 3, 20)  # Обычный день
    total_price = 333.33

    prepayment = service.calculate_prepayment(total_price, test_date)

    # 50% от 333.33 = 166.665, должно округлиться до 166.67
    expected = 166.67
    assert prepayment == expected, f"Expected {expected}, got {prepayment}"
    print(f"✓ Округление работает корректно: {prepayment}")

if __name__ == "__main__":
    print("Запуск тестов PrepaymentService...\n")

    try:
        test_standard_day_prepayment()
        test_holiday_prepayment()
        test_recurring_holiday()
        test_valentines_day()
        test_rounding()

        print("\n✓ Все тесты пройдены успешно!")
    except AssertionError as e:
        print(f"\n✗ Тест провален: {e}")
        exit(1)
    except Exception as e:
        print(f"\n✗ Ошибка при выполнении тестов: {e}")
        exit(1)
```

```bash
# Запустить тесты сервиса
python test_prepayment_service.py

# Ожидается: Все тесты проходят
# Если провалы: Исправить логику в PrepaymentService, повторить
```

### Уровень 4: Ручное тестирование в боте
```bash
# 1. Запустить бота в debug режиме
export ENV=debug
python src/main.py

# 2. В Telegram открыть бота @the_secret_house_booking_bot

# ТЕСТ 1: Обычный день (50% предоплата)
# Действия:
#   1. /start -> Забронировать дом
#   2. Выбрать дату: 15 марта 2026 (обычный день)
#   3. Выбрать тариф: "Суточно от 3 человек" (700 руб)
#   4. Пройти все шаги до сообщения об оплате
# Ожидается:
#   - Сообщение показывает: "Предоплата: 350 руб." (50% от 700)
#   - Нет упоминания праздника

# ТЕСТ 2: Новый год (100% предоплата)
# Действия:
#   1. Новое бронирование
#   2. Выбрать дату: 1 января 2026 (Новый год)
#   3. Выбрать тариф: "Суточно от 3 человек" (700 руб)
#   4. Пройти все шаги до сообщения об оплате
# Ожидается:
#   - Сообщение показывает: "Предоплата: 700 руб." (100% от 700)
#   - Есть текст: "🎉 Новый год - требуется полная предоплата"

# ТЕСТ 3: День Победы (100% предоплата)
# Действия:
#   1. Новое бронирование
#   2. Выбрать дату: 9 мая 2026
#   3. Выбрать тариф: "Рабочий" (180 руб)
#   4. Пройти все шаги до сообщения об оплате
# Ожидается:
#   - Сообщение показывает: "Предоплата: 180 руб." (100% от 180)
#   - Есть текст: "🎉 День Победы - требуется полная предоплата"

# ТЕСТ 4: Проверка сохранения в БД
# Действия:
#   1. Завершить одно из бронирований (загрузить чек)
#   2. Проверить в базе данных:
#      sqlite3 test_the_secret_house.db
#      SELECT id, start_date, price, prepayment_price FROM booking ORDER BY id DESC LIMIT 1;
# Ожидается:
#   - prepayment_price соответствует рассчитанному значению
#   - Для обычного дня: prepayment_price = price * 0.5
#   - Для праздника: prepayment_price = price

# ТЕСТ 5: Админ может изменить предоплату вручную
# Действия:
#   1. Войти как админ
#   2. /booking_list -> Выбрать бронирование
#   3. Изменить предоплату -> Ввести новую сумму (например, 100)
# Ожидается:
#   - Предоплата успешно обновляется на 100 руб
#   - Ручное изменение работает независимо от автоматического расчета
```

### Уровень 5: Проверка логов
```bash
# Во время тестирования проверить логи

# Для обычного дня должно быть:
# INFO: Standard prepayment calculation: 50% of 700.0 = 350.0

# Для праздника должно быть:
# INFO: Holiday prepayment calculation: Новый год, 100% of 700.0 = 700.0

# Проверить что нет ошибок загрузки правил:
# Не должно быть: FileNotFoundError, ValueError, JSON decode errors
```

## Финальный чеклист валидации

- [ ] Все Python файлы компилируются без ошибок
- [ ] JSON конфигурация загружается и валидируется
- [ ] PrepaymentService правильно рассчитывает 50% для обычных дней
- [ ] PrepaymentService правильно рассчитывает 100% для праздников
- [ ] Все праздники из списка добавлены в конфигурацию
- [ ] Повторяющиеся праздники корректно определяются каждый год
- [ ] Бот показывает правильную сумму предоплаты в сообщении
- [ ] Предоплата сохраняется в БД при завершении бронирования
- [ ] Администратор может вручную изменить предоплату
- [ ] Подарочные сертификаты все еще работают (100% предоплата)
- [ ] Логи содержат информацию о расчетах предоплаты
- [ ] Нет ошибок в логах при загрузке правил
- [ ] Округление работает корректно (2 знака после запятой)
- [ ] Бот не падает при неверных датах или пустых правилах

---

## Антипаттерны, которых следует избегать

- ❌ Не удаляйте константу PREPAYMENT из config.py - она может использоваться как fallback
- ❌ Не меняйте логику для подарочных сертификатов - там всегда 100%
- ❌ Не забывайте про округление - используйте round(value, 2)
- ❌ Не игнорируйте валидацию в __post_init__ - она критична для корректности данных
- ❌ Не используйте hardcoded списки праздников в коде - только через JSON конфигурацию
- ❌ Не ломайте существующую функциональность ручного изменения предоплаты администратором
- ❌ Не забывайте про логирование - оно помогает в отладке
- ❌ Не пропускайте тестирование граничных случаев (округление, переход года, etc.)
- ❌ Не используйте sync functions в async handlers - только async/await
- ❌ Не забывайте про encoding="utf-8" при открытии JSON файлов (кириллица!)

## Важные замечания

### Радуница - изменяемая дата
Радуница - это **переходящий праздник** (9-й день после православной Пасхи), дата меняется каждый год:
- 2026: 21 апреля
- 2027: 13 апреля
- 2028: 2 мая

**РЕШЕНИЕ**: Использовать `is_recurring: false` и конкретную дату на текущий год. Администратору нужно будет обновлять дату ежегодно в JSON конфигурации.

### Обработка нескольких правил на одну дату
Если несколько правил применяются к одной дате (например, Новый год и какое-то специальное событие), берем первое правило из списка. **Порядок в JSON файле важен**.

### Сохранение предоплаты в Redis
BookingDraft в Redis должен содержать рассчитанную предоплату ДО сохранения в БД, чтобы при создании BookingBase значение уже было известно.

### Обратная совместимость
Старые бронирования в БД могут иметь `prepayment_price = 80` (старая константа). Это нормально, не нужно их обновлять. Новая логика применяется только к новым бронированиям.

---

## Оценка уверенности: 9/10

Высокая уверенность благодаря:
+ Четко определенным требованиям (50% vs 100%)
+ Существующему похожему паттерну (DatePricingService)
+ Хорошо структурированной кодовой базе
+ Наличию всех необходимых инструментов (dataclasses, singleton, JSON)
+ Простой бизнес-логике (проверка даты + процент)

Небольшая неопределенность:
- Точное место вызова create_booking() может отличаться (нужна дополнительная проверка)
- Возможны edge cases с переходом года для повторяющихся праздников (но dataclass валидация поможет)

**Целевая оценка для одноэтапной реализации**: 8+ ✓ Достигнута

**Факторы, влияющие на оценку**:
- Ясность требований: +2
- Наличие похожих паттернов в кодовой базе: +2
- Полнота внешней документации (Python datetime, dataclasses): +2
- Исполнимые validation gates: +2
- Определенная стратегия обработки ошибок: +1

---

## Приложение А: Пример полного конфига holiday_prepayment_rules.json

```json
{
  "prepayment_rules": [
    {
      "rule_id": "new_year_dec_31",
      "date": "12-31",
      "is_recurring": true,
      "prepayment_percentage": 100,
      "name": "Новый год (31 декабря)",
      "is_active": true,
      "description": "Новогодние праздники - требуется полная предоплата"
    },
    {
      "rule_id": "new_year_jan_01",
      "date": "01-01",
      "is_recurring": true,
      "prepayment_percentage": 100,
      "name": "Новый год (1 января)",
      "is_active": true,
      "description": "Новогодние праздники - требуется полная предоплата"
    },
    {
      "rule_id": "new_year_jan_02",
      "date": "01-02",
      "is_recurring": true,
      "prepayment_percentage": 100,
      "name": "Новый год (2 января)",
      "is_active": true,
      "description": "Новогодние праздники - требуется полная предоплата"
    },
    {
      "rule_id": "christmas_orthodox",
      "date": "01-07",
      "is_recurring": true,
      "prepayment_percentage": 100,
      "name": "Рождество Христово (православное)",
      "is_active": true,
      "description": "Православное Рождество - требуется полная предоплата"
    },
    {
      "rule_id": "valentines_day",
      "date": "02-14",
      "is_recurring": true,
      "prepayment_percentage": 100,
      "name": "День всех влюбленных",
      "is_active": true,
      "description": "День святого Валентина - требуется полная предоплата"
    },
    {
      "rule_id": "defenders_day",
      "date": "02-23",
      "is_recurring": true,
      "prepayment_percentage": 100,
      "name": "День защитников Отечества",
      "is_active": true,
      "description": "23 февраля - требуется полная предоплата"
    },
    {
      "rule_id": "womens_day",
      "date": "03-08",
      "is_recurring": true,
      "prepayment_percentage": 100,
      "name": "Международный женский день",
      "is_active": true,
      "description": "8 марта - требуется полная предоплата"
    },
    {
      "rule_id": "radonitsa_2026",
      "date": "2026-04-21",
      "is_recurring": false,
      "prepayment_percentage": 100,
      "name": "Радуница",
      "is_active": true,
      "description": "Радуница 2026 года - требуется полная предоплата"
    },
    {
      "rule_id": "labor_day",
      "date": "05-01",
      "is_recurring": true,
      "prepayment_percentage": 100,
      "name": "Праздник труда",
      "is_active": true,
      "description": "1 мая - требуется полная предоплата"
    },
    {
      "rule_id": "victory_day",
      "date": "05-09",
      "is_recurring": true,
      "prepayment_percentage": 100,
      "name": "День Победы",
      "is_active": true,
      "description": "День Победы - требуется полная предоплата"
    },
    {
      "rule_id": "independence_day_belarus",
      "date": "07-03",
      "is_recurring": true,
      "prepayment_percentage": 100,
      "name": "День Независимости Республики Беларусь",
      "is_active": true,
      "description": "3 июля - требуется полная предоплата"
    },
    {
      "rule_id": "october_revolution",
      "date": "11-07",
      "is_recurring": true,
      "prepayment_percentage": 100,
      "name": "День Октябрьской революции",
      "is_active": true,
      "description": "7 ноября - требуется полная предоплата"
    },
    {
      "rule_id": "christmas_catholic",
      "date": "12-25",
      "is_recurring": true,
      "prepayment_percentage": 100,
      "name": "Рождество Христово (католическое)",
      "is_active": true,
      "description": "Католическое Рождество - требуется полная предоплата"
    }
  ]
}
```

---

**КОНЕЦ PRP**

**Создано**: 2026-01-31
**Версия**: 1.0
**Проект**: The Secret House Booking Bot
**Автор**: Claude Code AI Agent
