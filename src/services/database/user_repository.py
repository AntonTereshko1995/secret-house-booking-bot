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

    def update_user_contact(self, chat_id: int, contact: str) -> UserBase:
        """Update user's contact (phone/email). Creates user if not found."""
        with self.Session() as session:
            try:
                user = session.scalar(select(UserBase).where(UserBase.chat_id == chat_id))
                if not user:
                    # Try to find user by contact
                    user = session.scalar(select(UserBase).where(UserBase.contact == contact))
                    if user:
                        # Check if this chat_id is already assigned to a different user
                        existing_user_with_chat = session.scalar(
                            select(UserBase).where(
                                and_(
                                    UserBase.chat_id == chat_id,
                                    UserBase.id != user.id
                                )
                            )
                        )

                        if existing_user_with_chat:
                            # Remove chat_id from the other user
                            LoggerService.info(
                                __name__,
                                "Removing chat_id from different user in update_user_contact",
                                kwargs={
                                    "removed_from_user_id": existing_user_with_chat.id,
                                    "chat_id": chat_id,
                                    "assigned_to_user": user.id,
                                },
                            )
                            existing_user_with_chat.chat_id = None

                        # User exists with this contact but without chat_id - update it
                        user.chat_id = chat_id
                        session.commit()
                        session.refresh(user)
                        LoggerService.info(
                            __name__,
                            "Found user by contact, added chat_id",
                            kwargs={"user_id": user.id, "chat_id": chat_id, "contact": contact},
                        )
                        return user
                    else:
                        # Create new user
                        user = UserBase(chat_id=chat_id, contact=contact, is_active=True)
                        session.add(user)
                        session.commit()
                        session.refresh(user)
                        LoggerService.info(
                            __name__,
                            "Created new user with contact",
                            kwargs={"user_id": user.id, "chat_id": chat_id, "contact": contact},
                        )
                        return user

                # Check if contact is already assigned to another user
                existing_user = session.scalar(
                    select(UserBase).where(
                        and_(
                            UserBase.contact == contact,
                            UserBase.id != user.id
                        )
                    )
                )
                if existing_user:
                    # Merge data from existing_user into user (keep the one with chat_id)
                    user.contact = contact
                    user.has_bookings = max(user.has_bookings or 0, existing_user.has_bookings or 0)
                    user.total_bookings = (user.total_bookings or 0) + (existing_user.total_bookings or 0)
                    user.completed_bookings = (user.completed_bookings or 0) + (existing_user.completed_bookings or 0)

                    # Delete the duplicate user without chat_id
                    session.delete(existing_user)
                    session.commit()
                    session.refresh(user)

                    LoggerService.info(
                        __name__,
                        "Contact found for another user, merged data and deleted duplicate",
                        kwargs={
                            "deleted_user_id": existing_user.id,
                            "kept_user_id": user.id,
                            "chat_id": chat_id,
                            "contact": contact,
                        },
                    )
                    return user

                user.contact = contact
                session.commit()
                session.refresh(user)  # Refresh to keep object valid after session closes

                LoggerService.info(
                    __name__,
                    "Updated user contact",
                    kwargs={"chat_id": chat_id, "contact": contact},
                )
                return user

            except Exception as e:
                session.rollback()
                print(f"Error in update_user_contact: {e}")
                LoggerService.error(__name__, "update_user_contact", exception=e)
                raise

    def update_user_chat_id(self, user_name: str, chat_id: int) -> UserBase:
        """Update or set chat_id for user. Reactivates deactivated users. Handles duplicates gracefully."""
        with self.Session() as session:
            try:
                # Check if user with this chat_id already exists
                user = session.scalar(
                    select(UserBase).where(UserBase.chat_id == chat_id)
                )

                if user:
                    # User already has this chat_id, check if user_name needs update
                    if user_name and user.user_name != user_name:
                        user.user_name = user_name
                        session.commit()
                        session.refresh(user)
                        LoggerService.info(
                            __name__,
                            "Updated user_name for existing user",
                            kwargs={
                                "user_id": user.id,
                                "chat_id": chat_id,
                                "old_user_name": user.user_name,
                                "new_user_name": user_name,
                            },
                        )
                    else:
                        session.commit()  # Commit empty transaction to avoid ROLLBACK in logs
                        session.refresh(user)
                        LoggerService.info(
                            __name__,
                            "User already has this chat_id",
                            kwargs={
                                "user_id": user.id,
                                "chat_id": chat_id,
                                "user_name": user_name,
                            },
                        )
                    return user

                if not user:
                    if user_name is not None and user_name != "":
                        # Check if user with this user_name exists (including deactivated)
                        user = session.scalar(
                            select(UserBase).where(UserBase.user_name == user_name)
                        )

                        if user:
                            # Check if this chat_id is already assigned to a different user
                            existing_user_with_chat = session.scalar(
                                select(UserBase).where(
                                    and_(
                                        UserBase.chat_id == chat_id,
                                        UserBase.id != user.id
                                    )
                                )
                            )

                            if existing_user_with_chat:
                                # Remove chat_id from the other user (re-subscription scenario)
                                LoggerService.info(
                                    __name__,
                                    "Removing chat_id from different user",
                                    kwargs={
                                        "removed_from_user_id": existing_user_with_chat.id,
                                        "chat_id": chat_id,
                                        "assigned_to_user": user.id,
                                    },
                                )
                                existing_user_with_chat.chat_id = None

                            # Update existing user (possibly reactivating)
                            user.chat_id = chat_id
                            if not user.is_active:
                                user.is_active = True
                                LoggerService.info(
                                    __name__,
                                    "Reactivated deactivated user",
                                    kwargs={
                                        "user_id": user.id,
                                        "user_name": user_name,
                                        "new_chat_id": chat_id,
                                    },
                                )
                            session.commit()
                            session.refresh(user)
                            LoggerService.info(
                                __name__,
                                "Updated chat_id for user",
                                kwargs={
                                    "user_id": user.id,
                                    "chat_id": chat_id,
                                    "user_name": user_name,
                                },
                            )
                        else:
                            # Create new user if not found
                            # contact can be None initially, will be set later when user provides it
                            user = UserBase(
                                contact=None,
                                user_name=user_name,
                                chat_id=chat_id,
                                is_active=True,
                            )
                            session.add(user)
                            session.commit()
                            session.refresh(user)
                            LoggerService.info(
                                __name__,
                                "Created new user with chat_id",
                                kwargs={
                                    "user_id": user.id,
                                    "chat_id": chat_id,
                                    "user_name": user_name,
                                },
                            )
                    else:
                        # Create new user without user_name
                        # contact can be None initially, will be set later when user provides it
                        user = UserBase(
                            contact=None,
                            user_name=user_name,
                            chat_id=chat_id,
                            is_active=True,
                        )
                        session.add(user)
                        session.commit()
                        session.refresh(user)
                        LoggerService.info(
                            __name__,
                            "Created new user without user_name",
                            kwargs={
                                "user_id": user.id,
                                "chat_id": chat_id,
                            },
                        )

                return user

            except Exception as e:
                session.rollback()
                print(f"Error in update_user_chat_id: {e}")
                LoggerService.error(__name__, "update_user_chat_id", exception=e)
                raise

    def get_all_user_chat_ids(self) -> list[int]:
        """Get all chat IDs from active UserBase."""
        try:
            with self.Session() as session:
                # Use distinct() to get unique chat_ids from UserBase
                # Filter out null values and inactive users
                chat_ids = session.scalars(
                    select(UserBase.chat_id).where(
                        and_(UserBase.chat_id.isnot(None), UserBase.is_active == True)
                    )
                ).all()

                # Convert to list and return
                return list(chat_ids)
        except Exception as e:
            print(f"Error in get_all_user_chat_ids: {e}")
            LoggerService.error(__name__, "get_all_user_chat_ids", e)
            return []  # Return empty list on error

    def get_user_chat_ids_with_bookings(self) -> list[int]:
        """Get chat IDs of active users who have at least one booking."""
        try:
            with self.Session() as session:
                chat_ids = session.scalars(
                    select(UserBase.chat_id).where(
                        and_(
                            UserBase.chat_id.isnot(None),
                            UserBase.has_bookings == 1,
                            UserBase.is_active == True,
                        )
                    )
                ).all()
                return list(chat_ids)
        except Exception as e:
            print(f"Error in get_user_chat_ids_with_bookings: {e}")
            LoggerService.error(__name__, "get_user_chat_ids_with_bookings", e)
            return []

    def get_user_chat_ids_without_bookings(self) -> list[int]:
        """Get chat IDs of active users who have never made a booking."""
        try:
            with self.Session() as session:
                chat_ids = session.scalars(
                    select(UserBase.chat_id).where(
                        and_(
                            UserBase.chat_id.isnot(None),
                            UserBase.has_bookings == 0,
                            UserBase.is_active == True,
                        )
                    )
                ).all()
                return list(chat_ids)
        except Exception as e:
            print(f"Error in get_user_chat_ids_without_bookings: {e}")
            LoggerService.error(__name__, "get_user_chat_ids_without_bookings", e)
            return []

    def deactivate_user(self, chat_id: int) -> bool:
        """Deactivate user by chat_id (set is_active=False). Returns True if found."""
        try:
            with self.Session() as session:
                # Find user with this chat_id
                user = session.scalar(
                    select(UserBase).where(UserBase.chat_id == chat_id)
                )

                if user:
                    user.is_active = False
                    session.commit()
                    print(f"Deactivated user {user.id} with chat_id {chat_id}")
                    return True
                else:
                    return False
        except Exception as e:
            print(f"Error in deactivate_user: {e}")
            LoggerService.error(__name__, "deactivate_user", e)
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

    def get_total_users_count(self) -> int:
        """Get total count of users in system."""
        try:
            with self.Session() as session:
                from sqlalchemy import func

                count = session.scalar(select(func.count(UserBase.id)))
                return int(count) if count else 0
        except Exception as e:
            print(f"Error in get_total_users_count: {e}")
            LoggerService.error(__name__, "get_total_users_count", e)
            return 0

    def get_users_with_bookings_count(self) -> int:
        """Get count of users with at least one booking."""
        try:
            with self.Session() as session:
                from sqlalchemy import func

                count = session.scalar(
                    select(func.count(UserBase.id)).where(UserBase.has_bookings == 1)
                )
                return int(count) if count else 0
        except Exception as e:
            print(f"Error in get_users_with_bookings_count: {e}")
            LoggerService.error(__name__, "get_users_with_bookings_count", e)
            return 0

    def get_users_with_completed_count(self) -> int:
        """Get count of users with at least one completed booking."""
        try:
            with self.Session() as session:
                from sqlalchemy import func

                count = session.scalar(
                    select(func.count(UserBase.id)).where(
                        UserBase.completed_bookings > 0
                    )
                )
                return int(count) if count else 0
        except Exception as e:
            print(f"Error in get_users_with_completed_count: {e}")
            LoggerService.error(__name__, "get_users_with_completed_count", e)
            return 0

    def get_active_users_count(self) -> int:
        """Get count of active users."""
        try:
            with self.Session() as session:
                from sqlalchemy import func

                count = session.scalar(
                    select(func.count(UserBase.id)).where(UserBase.is_active == True)
                )
                return int(count) if count else 0
        except Exception as e:
            print(f"Error in get_active_users_count: {e}")
            LoggerService.error(__name__, "get_active_users_count", e)
            return 0

    def get_deactivated_users_count(self) -> int:
        """Get count of deactivated users."""
        try:
            with self.Session() as session:
                from sqlalchemy import func

                count = session.scalar(
                    select(func.count(UserBase.id)).where(UserBase.is_active == False)
                )
                return int(count) if count else 0
        except Exception as e:
            print(f"Error in get_deactivated_users_count: {e}")
            LoggerService.error(__name__, "get_deactivated_users_count", e)
            return 0

    def get_users_without_chat_id(self) -> list[UserBase]:
        """Get all users without chat_id."""
        try:
            with self.Session() as session:
                users = session.scalars(
                    select(UserBase).where(UserBase.chat_id.is_(None))
                ).all()
                return list(users)
        except Exception as e:
            print(f"Error in get_users_without_chat_id: {e}")
            LoggerService.error(__name__, "get_users_without_chat_id", e)
            return []
