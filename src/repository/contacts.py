from datetime import date, timedelta
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.database.models import Contact, User
from src.schemas.contacts import ContactModel
import logging

logger = logging.getLogger(__name__)


class ContactsRepository:
    """
    Repository for handling database operations related to contacts.
    """

    def __init__(self, session: AsyncSession):

        self.db = session

    async def fetch_contacts(
        self,
        user: User,
        firstname: Optional[str] = None,
        lastname: Optional[str] = None,
        email: Optional[str] = None,
        skip: int = 0,
        limit: int = 10,
    ) -> List[Contact]:
        """
        Fetches a list of contacts based on the given filters.

        Args:
            user: The user whose contacts are to be fetched.
            firstname: Optional filter by contact firstname.
            lastname: Optional filter by contact lastname.
            email: Optional filter by contact email.
            skip: Number of contacts to skip. Defaults to 0.
            limit: Number of contacts to return. Defaults to 10.

        Returns:
            List[Contact]: List of contacts matching the given filters.
        """
        if not user:
            logger.info("User not found in database")
            return []

        stmt = (
            select(Contact)
            .filter(Contact.user_id == user.id)
            .where(Contact.firstname.contains(firstname))
            .where(Contact.lastname.contains(lastname))
            .where(Contact.email.contains(email))
            .offset(skip)
            .limit(limit)
        )
        contacts = await self.db.execute(stmt)
        return contacts.scalars().all()

    async def get_contact_by_id(self, contact_id: int, user: User) -> Contact | None:
        """
        Fetches a contact by contact ID.

        Args:
            contact_id (int): The contact ID to fetch.
            user (User): The user whose contact is to be fetched.

        Returns:
            Contact | None: The fetched contact if found, otherwise None.
        """
        stmt = (
            select(Contact).filter_by(id=contact_id).filter(Contact.user_id == user.id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_contact(self, body: ContactModel, user: User) -> Contact:
        """
        Creates a new contact.

        Args:
            body (ContactModel): The contact data to be created.
            user (User): The user who is creating the contact.

        Returns:
            Contact: The created contact.

        Raises:
            ValueError: If contact with the given email or phone number already exists.
        """
        logger.info(type(user))

        contact = Contact(**body.model_dump(exclude_unset=True), user=user)
        contact.user_id = user.id

        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def update_contact(
        self, contact_id: int, body: ContactModel, user: User
    ) -> Contact | None:
        """
        Updates a contact by contact ID.

        Args:
            contact_id (int): The contact ID to update.
            body (ContactModel): The contact data to be updated.
            user (User): The user who is updating the contact.

        Returns:
            Contact | None: The updated contact if found, otherwise None.
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            for key, value in body.dict(exclude_unset=True).items():
                setattr(contact, key, value)
            await self.db.commit()
            await self.db.refresh(contact)
        return contact

    async def delete_contact(self, contact_id: int, user: User) -> Contact | None:
        """
        Deletes a contact by contact ID.

        Args:
            contact_id (int): The contact ID to delete.
            user (User): The user who is deleting the contact.

        Returns:
            Contact | None: The deleted contact if found, otherwise None.
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
            return contact
        return None

    async def is_contact(self, email: str, phonenumber: str, user: User) -> bool:
        """
        Checks if a contact exists by email or phone number.

        Args:
            email (str): Contact email to check.
            phonenumber (str): Contact phone number to check.
            user (User): The user who owns the contact.

        Returns:
            bool: True if contact exists, otherwise False.
        """
        query = (
            select(Contact)
            .filter(Contact.user_id == user.id)
            .where((Contact.email == email) | (Contact.phonenumber == phonenumber))
        )
        result = await self.db.execute(query)
        return result.scalars().first() is not None

    async def fetch_upcoming_birthdays(self, days: int, user: User) -> List[Contact]:
        """
        Fetches contacts with upcoming birthdays within the given number of days.

        Args:
            days (int): Number of days to look ahead for upcoming birthdays.
            user (User): The user who owns the contacts.

        Returns:
            List[Contact]: List of contacts with upcoming birthdays.
        """
        today = date.today()
        end_date = today + timedelta(days=days)

        stmt = (
            select(Contact)
            .filter(Contact.user_id == user.id)
            .where(
                or_(
                    and_(
                        func.date_part("month", Contact.birthday)
                        == func.date_part("month", today),
                        func.date_part("day", Contact.birthday).between(
                            func.date_part("day", today),
                            func.date_part("day", end_date),
                        ),
                    ),
                    and_(
                        func.date_part("month", Contact.birthday)
                        > func.date_part("month", today),
                        func.date_part("day", Contact.birthday)
                        <= func.date_part("day", end_date),
                    ),
                )
            )
            .order_by(
                func.date_part("month", Contact.birthday).asc(),
                func.date_part("day", Contact.birthday).asc(),
            )
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()
