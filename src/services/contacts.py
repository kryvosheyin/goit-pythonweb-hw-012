from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.repository.contacts import ContactsRepository
from src.schemas.contacts import ContactModel


class ContactService:
    def __init__(self, db_session: AsyncSession):
        self.contact_repo = ContactsRepository(db_session)

    async def create_new_contact(self, contact_data: ContactModel):
        if await self.contact_repo.is_contact_exists(
            contact_data.email, contact_data.phonenumber
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contact with email - '{contact_data.email}' or phone number - '{contact_data.phonenumber}' already exists.",
            )
        return await self.contact_repo.create_contact(contact_data)

    async def fetch_contacts(
        self,
        firstname: Optional[str] = None,
        lastname: Optional[str] = None,
        email: Optional[str] = None,
        skip: int = 0,
        limit: int = 10,
    ):
        return await self.contact_repo.fetch_contacts(
            firstname, lastname, email, skip, limit
        )

    async def fetch_contact_by_id(self, contact_id: int):
        contact = await self.contact_repo.get_contact_by_id(contact_id)
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contact with ID {contact_id} not found.",
            )
        return contact

    async def update_exist_contact(self, contact_id: int, contact_data: ContactModel):
        updated_contact = await self.contact_repo.update_contact(
            contact_id, contact_data
        )
        if not updated_contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contact with ID {contact_id} not found for update.",
            )
        return updated_contact

    async def delete_contact(self, contact_id: int):
        deletion_success = await self.contact_repo.delete_contact(contact_id)
        if not deletion_success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contact with ID {contact_id} not found for deletion.",
            )
        return {"message": f"Contact with ID {contact_id} successfully deleted."}

    async def fetch_upcoming_birthdays(self, days_ahead: int):
        return await self.contact_repo.fetch_upcoming_birthdays(days_ahead)