"""Helper functions for formatting statistics messages."""

from src.services.statistics_service import (
    Statistics,
    BookingStats,
    UserStats,
    GiftStats,
)


def format_statistics_message(stats: Statistics) -> str:
    """Format statistics into beautiful Telegram HTML message."""

    msg = "<b>📊 СТАТИСТИКА БРОНИРОВАНИЙ</b>\n"
    msg += f"🕐 Сгенерировано: {stats.generated_at.strftime('%d.%m.%Y %H:%M')}\n\n"

    # All-time section
    msg += "<b>📈 ВСЕ ВРЕМЯ</b>\n"
    msg += format_booking_stats_section(stats.all_time)
    msg += "\n"

    # Year-to-date
    msg += f"<b>📅 ГОД ({stats.generated_at.year})</b>\n"
    msg += format_booking_stats_section(stats.year_to_date)
    msg += "\n"

    # Current month
    month_names = [
        "Январь",
        "Февраль",
        "Март",
        "Апрель",
        "Май",
        "Июнь",
        "Июль",
        "Август",
        "Сентябрь",
        "Октябрь",
        "Ноябрь",
        "Декабрь",
    ]
    current_month_name = month_names[stats.generated_at.month - 1]
    msg += f"<b>📆 ТЕКУЩИЙ МЕСЯЦ ({current_month_name})</b>\n"
    msg += format_booking_stats_section(stats.current_month)
    msg += "\n"

    # Users
    msg += "<b>👥 ПОЛЬЗОВАТЕЛИ</b>\n"
    msg += format_user_stats_section(stats.users)
    msg += "\n"

    # Gifts
    msg += "<b>🎁 ПОДАРОЧНЫЕ СЕРТИФИКАТЫ</b>\n"
    msg += format_gift_stats_section(stats.gifts)
    msg += "\n"

    # Total revenue
    msg += "<b>💎 ОБЩАЯ ПРИБЫЛЬ</b>\n"
    msg += f"├ От броней: {stats.all_time.total_revenue:,.0f} руб.\n"
    msg += f"├ От сертификатов: {stats.gifts.gift_revenue:,.0f} руб.\n"
    msg += f"└ <b>Итого: {stats.total_revenue:,.0f} руб.</b>\n"

    return msg


def format_booking_stats_section(stats: BookingStats) -> str:
    """Format booking statistics section."""
    section = f"├ Всего броней: <b>{stats.total_bookings:,}</b>\n"
    section += f"├ ✅ Выполнено: {stats.completed_bookings:,}\n"
    section += f"├ ❌ Отменено: {stats.canceled_bookings:,}\n"
    section += f"├ 🏃 Активных: {stats.active_bookings:,}\n"
    section += f"├ 💰 Выручка: <b>{stats.total_revenue:,.0f}</b> руб.\n"
    section += f"└ 💵 Средний чек: {stats.average_price:,.0f} руб.\n"
    return section


def format_user_stats_section(stats: UserStats) -> str:
    """Format user statistics section."""
    section = f"├ Всего: {stats.total_users:,}\n"
    section += f"├ 🟢 Активных: {stats.active_users:,}\n"
    section += f"├ 🔴 Деактивированных: {stats.deactivated_users:,}\n"
    section += f"├ С бронями: {stats.users_with_bookings:,}\n"
    section += f"├ Завершили: {stats.users_with_completed:,}\n"
    section += f"├ Конверсия: {stats.conversion_rate:.1f}%\n"
    section += f"└ Среднее броней: {stats.avg_bookings_per_user:.1f}\n"
    return section


def format_gift_stats_section(stats: GiftStats) -> str:
    """Format gift certificate statistics section."""
    section = f"├ Всего: {stats.total_gifts:,}\n"
    section += f"├ 💳 Оплачено: {stats.paid_gifts:,}\n"
    section += f"├ ✅ Использовано: {stats.used_gifts:,}\n"
    section += f"├ ⏳ Не использовано: {stats.unused_gifts:,}\n"
    section += f"└ 💰 Выручка: <b>{stats.gift_revenue:,.0f}</b> руб.\n"
    return section
