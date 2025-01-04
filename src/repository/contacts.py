from datetime import date, timedelta
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.database.models import Contact
from src.schemas.contacts import ContactModel


class ContactsRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def fetch_contacts(
        self,
        firstname: Optional[str] = None,
        lastname: Optional[str] = None,
        email: Optional[str] = None,
        skip: int = 0,
        limit: int = 10,
    ) -> List[Contact]:
        stmt = select(Contact)

        if firstname:
            stmt = stmt.where(Contact.firstname.contains(firstname))
        if lastname:
            stmt = stmt.where(Contact.lastname.contains(lastname))
        if email:
            stmt = stmt.where(Contact.email.contains(email))

        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_contact_by_id(self, contact_id: int) -> Optional[Contact]:
        stmt = select(Contact).filter_by(id=contact_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_contact(self, body: ContactModel) -> Contact:
        contact = Contact(**body.model_dump(exclude_unset=True))
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def update_contact(
        self, contact_id: int, body: ContactModel
    ) -> Optional[Contact]:
        contact = await self.get_contact_by_id(contact_id)
        if contact:
            for key, value in body.model_dump(exclude_unset=True).items():
                setattr(contact, key, value)
            await self.db.commit()
            await self.db.refresh(contact)
        return contact

    async def delete_contact(self, contact_id: int) -> Optional[Contact]:
        contact = await self.get_contact_by_id(contact_id)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def is_contact_exists(self, email: str, phone_number: str) -> bool:
        stmt = select(Contact).where(
            or_(Contact.email == email, Contact.phonenumber == phone_number)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first() is not None

    async def fetch_upcoming_birthdays(self, days: int) -> List[Contact]:
        today = date.today()
        end_date = today + timedelta(days=days)

        stmt = (
            select(Contact)
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