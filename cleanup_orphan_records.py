#!/usr/bin/env python3
"""
Скрипт для очистки сиротских записей (orphan records) в SQLite базе данных.

Сиротские записи - это записи в дочерних таблицах, которые ссылаются на
несуществующие записи в родительских таблицах (нарушение foreign key).

Использование:
    python cleanup_orphan_records.py the_secret_house.db
"""

import sys
import sqlite3
from datetime import datetime


def backup_database(db_path: str) -> str:
    """Создать бэкап базы данных."""
    import shutil
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, backup_path)
    print(f"✓ Backup created: {backup_path}")
    return backup_path


def find_orphan_bookings(conn: sqlite3.Connection) -> list:
    """Найти бронирования без пользователей."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.id, b.user_id, b.start_date, b.end_date
        FROM booking b
        WHERE b.user_id NOT IN (SELECT id FROM user)
        ORDER BY b.id
    """)
    return cursor.fetchall()


def find_orphan_gifts(conn: sqlite3.Connection) -> list:
    """Найти подарки без пользователей."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT g.id, g.user_id
        FROM gift g
        WHERE g.user_id NOT IN (SELECT id FROM user)
        ORDER BY g.id
    """)
    return cursor.fetchall()


def find_orphan_bookings_by_gift(conn: sqlite3.Connection) -> list:
    """Найти бронирования со ссылками на несуществующие подарки."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.id, b.gift_id
        FROM booking b
        WHERE b.gift_id IS NOT NULL
        AND b.gift_id NOT IN (SELECT id FROM gift)
        ORDER BY b.id
    """)
    return cursor.fetchall()


def cleanup_orphans(db_path: str, dry_run: bool = True) -> None:
    """
    Очистить сиротские записи из базы данных.

    Args:
        db_path: Путь к SQLite базе данных
        dry_run: Если True, только показать что будет удалено (не удалять)
    """

    # Создать бэкап
    if not dry_run:
        backup_database(db_path)

    # Подключиться к базе
    conn = sqlite3.connect(db_path)

    print("\n" + "=" * 80)
    print("ПОИСК СИРОТСКИХ ЗАПИСЕЙ")
    print("=" * 80 + "\n")

    # 1. Найти бронирования без пользователей
    orphan_bookings = find_orphan_bookings(conn)
    print(f"Бронирования без пользователей: {len(orphan_bookings)}")
    if orphan_bookings:
        print("\nПримеры:")
        for booking_id, user_id, start_date, end_date in orphan_bookings[:5]:
            print(f"  - Booking ID: {booking_id}, User ID: {user_id}, Dates: {start_date} - {end_date}")
        if len(orphan_bookings) > 5:
            print(f"  ... и еще {len(orphan_bookings) - 5} записей")

    # 2. Найти подарки без пользователей
    orphan_gifts = find_orphan_gifts(conn)
    print(f"\nПодарки без пользователей: {len(orphan_gifts)}")
    if orphan_gifts:
        print("\nПримеры:")
        for gift_id, user_id in orphan_gifts[:5]:
            print(f"  - Gift ID: {gift_id}, User ID: {user_id}")
        if len(orphan_gifts) > 5:
            print(f"  ... и еще {len(orphan_gifts) - 5} записей")

    # 3. Найти бронирования со ссылками на несуществующие подарки
    orphan_bookings_by_gift = find_orphan_bookings_by_gift(conn)
    print(f"\nБронирования со ссылками на несуществующие подарки: {len(orphan_bookings_by_gift)}")
    if orphan_bookings_by_gift:
        print("\nПримеры:")
        for booking_id, gift_id in orphan_bookings_by_gift[:5]:
            print(f"  - Booking ID: {booking_id}, Gift ID: {gift_id}")
        if len(orphan_bookings_by_gift) > 5:
            print(f"  ... и еще {len(orphan_bookings_by_gift) - 5} записей")

    # Итого
    total_orphans = len(orphan_bookings) + len(orphan_gifts) + len(orphan_bookings_by_gift)

    print("\n" + "=" * 80)
    print(f"ВСЕГО НАЙДЕНО СИРОТСКИХ ЗАПИСЕЙ: {total_orphans}")
    print("=" * 80 + "\n")

    if total_orphans == 0:
        print("✓ База данных чистая! Сиротских записей не найдено.")
        conn.close()
        return

    # Удаление
    if dry_run:
        print("⚠️  DRY RUN MODE - записи НЕ будут удалены")
        print("Запустите с флагом --execute для реального удаления:")
        print(f"  python {sys.argv[0]} {db_path} --execute\n")
    else:
        print("🗑️  УДАЛЕНИЕ СИРОТСКИХ ЗАПИСЕЙ...\n")

        cursor = conn.cursor()

        # Удалить бронирования без пользователей
        if orphan_bookings:
            cursor.execute("""
                DELETE FROM booking
                WHERE user_id NOT IN (SELECT id FROM user)
            """)
            print(f"✓ Удалено {len(orphan_bookings)} бронирований без пользователей")

        # Удалить подарки без пользователей
        if orphan_gifts:
            cursor.execute("""
                DELETE FROM gift
                WHERE user_id NOT IN (SELECT id FROM user)
            """)
            print(f"✓ Удалено {len(orphan_gifts)} подарков без пользователей")

        # Очистить gift_id в бронированиях со ссылками на несуществующие подарки
        if orphan_bookings_by_gift:
            cursor.execute("""
                UPDATE booking
                SET gift_id = NULL
                WHERE gift_id IS NOT NULL
                AND gift_id NOT IN (SELECT id FROM gift)
            """)
            print(f"✓ Очищено gift_id в {len(orphan_bookings_by_gift)} бронированиях")

        conn.commit()

        print("\n" + "=" * 80)
        print("✓ ОЧИСТКА ЗАВЕРШЕНА УСПЕШНО")
        print("=" * 80)

    conn.close()


def main():
    """Главная функция."""
    if len(sys.argv) < 2:
        print("Usage: python cleanup_orphan_records.py <database.db> [--execute]")
        print("\nПримеры:")
        print("  # Проверить без удаления (dry run)")
        print("  python cleanup_orphan_records.py the_secret_house.db")
        print()
        print("  # Удалить сиротские записи")
        print("  python cleanup_orphan_records.py the_secret_house.db --execute")
        sys.exit(1)

    db_path = sys.argv[1]
    dry_run = "--execute" not in sys.argv

    try:
        cleanup_orphans(db_path, dry_run)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
