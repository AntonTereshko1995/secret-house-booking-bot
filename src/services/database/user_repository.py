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

                new_user = self.add_user(contact)
                return new_user
            except Exception as e:
                print(f"Error in get_or_create_user: {e}")
                LoggerService.error(__name__, "get_or_create_user", e)

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

    def get_user_by_chat_id(self, chat_id: int) -> UserBase:
        """Get user by chat_id."""
        try:
            with self.Session() as session:
                user = session.scalar(
                    select(UserBase).where(UserBase.chat_id == chat_id)
                )
                return user
        except Exception as e:
            print(f"Error in get_user_by_chat_id: {e}")
            LoggerService.error(__name__, "get_user_by_chat_id", e)
            return None

    def update_user_contact(self, user_id: int, contact: str) -> UserBase:
        """Update user's contact (phone/email)."""
        with self.Session() as session:
            try:
                user = session.scalar(
                    select(UserBase).where(UserBase.id == user_id)
                )
                if not user:
                    raise ValueError(f"User with id {user_id} not found")

                user.contact = contact
                session.commit()

                LoggerService.info(
                    __name__,
                    "Updated user contact",
                    kwargs={"user_id": user_id, "contact": contact}
                )
                return user

            except Exception as e:
                session.rollback()
                print(f"Error in update_user_contact: {e}")
                LoggerService.error(__name__, "update_user_contact", exception=e)
                raise

    def update_user_chat_id(self, user_name: str, chat_id: int) -> UserBase:
        """Update or set chat_id for user. Handles duplicates gracefully."""
        with self.Session() as session:
            try:
                # Get or create user by contact
                user = session.scalar(
                    select(UserBase).where(UserBase.chat_id == chat_id)
                )
                if not user:
                    if user_name != None and user_name != "":
                        user = session.scalar(
                            select(UserBase).where(UserBase.user_name == user_name)
                        )
                        user.chat_id = chat_id
                        session.commit()
                    else:
                        user = UserBase(user_name=user_name, chat_id=chat_id)
                        session.add(user)
                        session.commit()

                LoggerService.info(
                    __name__,
                    "Updated chat_id for user",
                    kwargs={"user_id": user.id, "chat_id": chat_id, "user_name": user_name},
                )

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

    def increment_completed_bookings(self, user_id: int) -> None:
        """Increment completed booking counter for user."""
        try:
            with self.Session() as session:
                user = session.scalar(select(UserBase).where(UserBase.id == user_id))
                if user:
                    user.completed_bookings = (user.completed_bookings or 0) + 1
                    session.commit()
        except Exception as e:
            LoggerService.error(__name__, "increment_completed_bookings", e)
