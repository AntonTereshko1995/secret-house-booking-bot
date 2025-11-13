import sys
import os
import pytz

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import logging
from src.services.logger_service import LoggerService
from src.handlers import admin_handler
from datetime import date, time, timedelta
from telegram import Update
from telegram.ext import Application, CallbackContext, JobQueue
from singleton_decorator import singleton
from src.services.database_service import DatabaseService
from src.services.chat_validation_service import ChatValidationService

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
            context.job_queue.run_daily(
                self.send_booking_details, time=job_time, name="send_booking_details"
            )
        if not context.job_queue.get_jobs_by_name("send_feeback"):
            context.job_queue.run_daily(
                self.send_feeback, time=job_time, name="send_feeback"
            )
        if not context.job_queue.get_jobs_by_name("cleanup_invalid_chats"):
            # Run weekly - every 7 days, first run 10 seconds after start for testing
            context.job_queue.run_repeating(
                self.cleanup_invalid_chats,
                interval=timedelta(days=7),
                first=timedelta(seconds=10),
                name="cleanup_invalid_chats",
            )
        if not context.job_queue.get_jobs_by_name("cleanup_expired_promocodes"):
            # Run daily at midnight (00:00)
            context.job_queue.run_daily(
                self.cleanup_expired_promocodes,
                time=time(0, 0, tzinfo=timezone),
                name="cleanup_expired_promocodes",
            )

    async def send_booking_details(self, context: CallbackContext):
        tomorrow = date.today() + timedelta(days=1)
        # bookings = database_service.get_booking_by_start_date(tomorrow)
        bookings = database_service.get_booking_by_period(date.today(), tomorrow)
        LoggerService.info(
            __name__,
            f"Found {len(bookings)} bookings for {tomorrow}",
            kwargs={"bookings_count": len(bookings), "date": str(tomorrow)},
        )

        for booking in bookings:
            try:
                await admin_handler.send_booking_details(context, booking)
                LoggerService.info(
                    __name__,
                    "Successfully sent booking details to user",
                    kwargs={
                        "chat_id": booking.user.chat_id,
                        "booking_id": booking.id,
                        "action": "send_booking_details",
                    },
                )
            except Exception as e:
                LoggerService.error(
                    __name__,
                    "Failed to send booking details to user",
                    exception=e,
                    kwargs={
                        "chat_id": booking.user.chat_id if booking.user else None,
                        "booking_id": booking.id,
                        "action": "send_booking_details",
                    },
                )

    async def send_feeback(self, context: CallbackContext):
        yesterday = date.today() - timedelta(days=1)
        bookings = database_service.get_booking_by_finish_date(yesterday)
        if not bookings:
            LoggerService.info(
                __name__,
                f"No completed bookings found for {yesterday}",
                kwargs={"date": str(yesterday)},
            )
            return

        LoggerService.info(
            __name__,
            f"Found {len(bookings)} completed bookings for {yesterday}",
            kwargs={"bookings_count": len(bookings), "date": str(yesterday)},
        )

        for booking in bookings:
            try:
                database_service.update_booking(booking.id, is_done=True)
                await admin_handler.send_feedback(context, booking)
                LoggerService.info(
                    __name__,
                    "Successfully sent feedback request to user",
                    kwargs={
                        "chat_id": booking.user.chat_id,
                        "booking_id": booking.id,
                        "action": "send_feedback",
                    },
                )
            except Exception as e:
                LoggerService.error(
                    __name__,
                    "Failed to send feedback request to user",
                    exception=e,
                    kwargs={
                        "chat_id": booking.user.chat_id,
                        "booking_id": booking.id,
                        "action": "send_feedback",
                    },
                )

    async def cleanup_invalid_chats(self, context: CallbackContext):
        """Weekly job to validate all chat IDs and remove invalid ones."""
        try:
            # Get all chat IDs from users
            chat_ids = database_service.get_all_user_chat_ids()

            if not chat_ids:
                LoggerService.info(
                    __name__, "No chat IDs to validate", kwargs={"chat_count": 0}
                )
                return

            LoggerService.info(
                __name__,
                "Starting weekly chat validation",
                kwargs={"total_chats": len(chat_ids)},
            )

            # Validate all chat IDs
            validation_service = ChatValidationService()
            results = await validation_service.validate_all_chat_ids(
                self._application.bot, chat_ids
            )

            # Deactivate users with invalid chat IDs
            deactivated_count = 0
            for invalid_chat_id in results["invalid_ids"]:
                try:
                    if database_service.deactivate_user(invalid_chat_id):
                        deactivated_count += 1
                        LoggerService.info(
                            __name__,
                            "Deactivated user with invalid chat_id",
                            kwargs={"chat_id": invalid_chat_id},
                        )
                except Exception as e:
                    LoggerService.error(
                        __name__,
                        "Failed to deactivate user",
                        exception=e,
                        kwargs={"chat_id": invalid_chat_id},
                    )

            # Log summary
            LoggerService.info(
                __name__,
                "Weekly chat cleanup completed",
                kwargs={
                    "total_checked": results["total_checked"],
                    "valid": results["valid"],
                    "invalid": results["invalid"],
                    "deactivated": deactivated_count,
                },
            )

        except Exception as e:
            LoggerService.error(__name__, "Weekly chat cleanup failed", exception=e)

    async def cleanup_expired_promocodes(self, context: CallbackContext):
        """Daily job to deactivate expired promocodes."""
        try:
            count = database_service.deactivate_expired_promocodes()
            if count > 0:
                LoggerService.info(
                    __name__,
                    "Expired promocodes cleanup completed",
                    kwargs={
                        "deactivated_count": count,
                        "date": str(date.today()),
                    },
                )
            else:
                LoggerService.info(
                    __name__,
                    "No expired promocodes to clean up",
                    kwargs={"date": str(date.today())},
                )

        except Exception as e:
            LoggerService.error(
                __name__, "Expired promocodes cleanup failed", exception=e
            )
