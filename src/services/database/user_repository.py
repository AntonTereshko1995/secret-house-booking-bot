import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.services.database.base import BaseRepository
from src.services.logger_service import LoggerService
from db.models.user import UserBase
from singleton_decorator import singleton
from sqlalchemy import and_, select


@singleton
class UserRepository(BaseRepository):
    """Repository for user-related database operations."""

    def add_user(self, contact: str) -> UserBase:
        """Add a new user to the database."""
        with self.Session() as session:
            try:
                new_user = UserBase(contact=contact)
                session.add(new_user)
                session.commit()
                print(f"User added: {new_user}")
                return new_user
            except Exception as e:
                session.rollback()
                print(f"Error adding user: {e}")
                LoggerService.error(__name__, "add_user", e)

    def get_or_create_user(self, contact: str) -> UserBase:
        """Get existing user or create new one."""
        with self.Session() as session:
            try:
                user = session.scalar(
                    select(UserBase).where(UserBase.contact == contact)
                )
                if user:
                    print(f"User already exists: {user}")
                    return user

                new_user = UserBase(contact=contact)
                session.add(new_user)
                session.commit()
                print(f"User created: {new_user}")
                return new_user
            except Exception as e:
                print(f"Error in get_or_create_user: {e}")
                LoggerService.error(__name__, "get_or_create_user", e)
                session.rollback()

    def get_user_by_contact(self, contact: str) -> UserBase:
        """Get user by contact (username or phone)."""
        try:
            with self.Session() as session:
                user = session.scalar(
                    select(UserBase).where(UserBase.contact == contact)
                )
                return user
        except Exception as e:
            print(f"Error in get_user_by_contact: {e}")
            LoggerService.error(__name__, "get_user_by_contact", e)

    def get_user_by_id(self, user_id: int) -> UserBase:
        """Get user by ID."""
        try:
            with self.Session() as session:
                user = session.scalar(select(UserBase).where(UserBase.id == user_id))
                return user
        except Exception as e:
            print(f"Error in get_user_by_id: {e}")
            LoggerService.error(__name__, "get_user_by_id", e)

    def update_user_chat_id(self, contact: str, chat_id: int) -> UserBase:
        """Update or set chat_id for user. Handles duplicates gracefully."""
        with self.Session() as session:
            try:
                # Get or create user by contact
                user = session.scalar(
                    select(UserBase).where(UserBase.contact == contact)
                )
                if not user:
                    user = UserBase(contact=contact)
                    session.add(user)
                    session.flush()  # Flush to get user.id

                # Check if this chat_id is already assigned to different user
                existing_user = session.scalar(
                    select(UserBase).where(
                        and_(
                            UserBase.chat_id == chat_id,
                            UserBase.id != user.id
                        )
                    )
                )

                # If chat_id exists for different user, remove it (re-subscribe scenario)
                if existing_user:
                    LoggerService.info(
                        __name__,
                        f"Removing chat_id {chat_id} from user {existing_user.id}",
                        kwargs={"old_user_id": existing_user.id}
                    )
                    existing_user.chat_id = None

                # Set chat_id for current user
                user.chat_id = chat_id
                session.commit()

                LoggerService.info(__name__, "Updated chat_id for user", kwargs={
                    "user_id": user.id, "chat_id": chat_id, "contact": contact
                })
                return user

            except Exception as e:
                session.rollback()
                print(f"Error in update_user_chat_id: {e}")
                LoggerService.error(__name__, "update_user_chat_id", exception=e)
                raise

    def get_all_user_chat_ids(self) -> list[int]:
        """Get all chat IDs from UserBase."""
        try:
            with self.Session() as session:
                # Use distinct() to get unique chat_ids from UserBase
                # Filter out null values
                chat_ids = session.scalars(
                    select(UserBase.chat_id).where(UserBase.chat_id.isnot(None))
                ).all()

                # Convert to list and return
                return list(chat_ids)
        except Exception as e:
            print(f"Error in get_all_user_chat_ids: {e}")
            LoggerService.error(__name__, "get_all_user_chat_ids", e)
            return []  # Return empty list on error

    def remove_user_chat_id(self, chat_id: int) -> bool:
        """Remove chat_id from user (set to None). Returns True if found."""
        try:
            with self.Session() as session:
                # Find user with this chat_id
                user = session.scalar(
                    select(UserBase).where(UserBase.chat_id == chat_id)
                )

                if user:
                    user.chat_id = None
                    session.commit()
                    print(f"Removed chat_id {chat_id} from user {user.id}")
                    return True
                else:
                    return False
        except Exception as e:
            print(f"Error in remove_user_chat_id: {e}")
            LoggerService.error(__name__, "remove_user_chat_id", e)
            return False

    def increment_booking_count(self, user_id: int) -> None:
        """Increment booking counters for user."""
        try:
            with self.Session() as session:
                user = session.scalar(select(UserBase).where(UserBase.id == user_id))
                if user:
                    user.has_bookings = 1
                    user.total_bookings = (user.total_bookings or 0) + 1
                    session.commit()
        except Exception as e:
            LoggerService.error(__name__, "increment_booking_count", e)
