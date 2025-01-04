from datetime import date, timedelta
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.database.models import Contact, User
from src.schemas.contacts import ContactModel


class ContactsRepository:
    """
    Contacts Repository class
    """

    def __init__(self, session: AsyncSession):
        """
        Init a ContactRepository

        Args:
            session: An AsyncSession object connected to the database.
        """

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
        Fetch contacts

        Args:
            firstname (str): Contacts first name
            lastname (str): Contacts last name
            email (str): Contacts email
            skip (int): The number of Contacts to skip
            limit (int): The maximum number of Contacts
            user (User): The owner of the Contacts

        Returns:
            A list of Contacts
        """

        stmt = (
            select(Contact)
            .filter_by(user=user)
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
        Fetch contact by ID

        Args:
            contact_id (int): Contact ID
            user (User): Contact user

        Returns:
            Contact with ID
        """

        stmt = select(Contact).filter_by(id=contact_id, user=user)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_contact(self, body: ContactModel, user: User) -> Contact:
        """
        Create contact

        Args:
            body (ContactModel): ContactModel
            user (User): Contact user

        Returns:
            A Contact with attributes
        """

        contact = Contact(**body.model_dump(exclude_unset=True), user=user)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def update_contact(
        self, contact_id: int, body: ContactModel, user: User
    ) -> Contact | None:
        """
        Update contact

        Args:
            contact_id (int): Contact ID
            body (ContactModel): ContactModel
            user (User): Contact user

        Returns:
            Updated Contact
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
        Delete contact by ID

        Args:
            contact_id (int): Contact ID
            user (User): Contact user

        Returns:
            Deleted Contact
        """

        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def is_contact(self, email: str, phonenumber: str, user: User) -> bool:
        """
        Check contact

        Args:
            email (str): Contact email
            phonenumber (str): Contact phone number
            user (User): Contact user

        Returns:
            True if the Contact exists, False - not
        """

        query = (
            select(Contact)
            .filter_by(user=user)
            .where((Contact.email == email) | (Contact.phonenumber == phonenumber))
        )
        result = await self.db.execute(query)
        return result.scalars().first() is not None

    async def fetch_upcoming_birthdays(self, days: int, user: User) -> List[Contact]:
        """
        Fetch contact upcoming birthdays

        Args:
            days (int): The number of days in the future to check.
            user (User): The owner of the Contacts to check.

        Returns:
            List contact upcoming birthdays
        """

        today = date.today()
        end_date = today + timedelta(days=days)

        stmt = (
            select(Contact)
            .filter_by(user=user)
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
