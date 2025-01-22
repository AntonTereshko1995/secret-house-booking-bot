import schedule
import time

def send_reminder():
    print("Напоминание отправлено!")

def run_reminder_jobs():
    # Запуск задач по расписанию
    schedule.every().day.at("09:00").do(send_reminder)

    while True:
        schedule.run_pending()
        time.sleep(1)