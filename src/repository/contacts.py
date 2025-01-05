from datetime import date, timedelta
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.database.models import Contact, User
from src.schemas.contacts import ContactModel
import logging

logger = logging.getLogger(__name__)


class ContactsRepository:

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

        stmt = (
            select(Contact).filter_by(id=contact_id).filter(Contact.user_id == user.id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_contact(self, body: ContactModel, user: User) -> Contact:

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

        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            for key, value in body.dict(exclude_unset=True).items():
                setattr(contact, key, value)
            await self.db.commit()
            await self.db.refresh(contact)
        return contact

    async def delete_contact(self, contact_id: int, user: User) -> Contact | None:

        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
            return contact
        return None

    async def is_contact(self, email: str, phonenumber: str, user: User) -> bool:

        query = (
            select(Contact)
            .filter(Contact.user_id == user.id)
            .where((Contact.email == email) | (Contact.phonenumber == phonenumber))
        )
        result = await self.db.execute(query)
        return result.scalars().first() is not None

    async def fetch_upcoming_birthdays(self, days: int, user: User) -> List[Contact]:

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
