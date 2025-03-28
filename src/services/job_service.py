import sys
import os
import pytz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import logging
from src.handlers import admin_handler
from datetime import date, time, timedelta
from telegram import Update
from telegram.ext import Application, CallbackContext, JobQueue
from singleton_decorator import singleton
from src.services.database_service import DatabaseService

logging.basicConfig(level=logging.INFO)
database_service = DatabaseService()

@singleton
class JobService:
    def __init__(self):
        self._application: Application

    def set_application(self, value: Application):
        self._application = value

    async def init_job(self, update: Update, context: CallbackContext):
        job_queue = self._application.job_queue
        if job_queue is None:
            job_queue = JobQueue()
            job_queue.set_application(self._application)

        self.register_jobs(update, context)
        await job_queue.start()

    def register_jobs(self, update: Update, context: CallbackContext):
        timezone = pytz.timezone("Europe/Minsk")
        job_time = time(8, 0, tzinfo=timezone)

        if not context.job_queue.get_jobs_by_name("send_booking_details"):
            context.job_queue.run_daily(self.send_booking_details, time=job_time, name="send_booking_details")
        if not context.job_queue.get_jobs_by_name("send_feeback"):
            context.job_queue.run_daily(self.send_feeback, time=job_time, name="send_feeback")
            
    async def send_booking_details(self, context: CallbackContext):
        tomorrow = date.today() + timedelta(days=1)
        bookings = database_service.get_booking_by_start_date(tomorrow)
        if not bookings:
            return
        
        for booking in bookings:
            await admin_handler.send_booking_details(context, booking)

    async def send_feeback(self, context: CallbackContext):
        yesterday = date.today() - timedelta(days=1)
        bookings = database_service.get_booking_by_finish_date(yesterday)
        if not bookings:
            return

        for booking in bookings:
            database_service.update_booking(booking.id, is_done=True)
            await admin_handler.send_feedback(context, booking)