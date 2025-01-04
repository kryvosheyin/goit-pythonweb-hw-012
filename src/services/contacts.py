from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.database.models import Contact, User
from src.repository.contacts import ContactsRepository
from src.schemas.contacts import ContactModel


class ContactService:
    def __init__(self, db_session: AsyncSession):
        """
        Init Contact Service class.

        Args:
            db (AsyncSession): SQLAlchemy database session.
        """

        self.contact_repo = ContactsRepository(db_session)

    async def create_new_contact(
        self, contact_data: ContactModel, user: User
    ) -> Contact:
        """
        Create new contact

        Args:
            contact_data (ContactModel): Data
            user (User): Contact user

        Returns:
            Contact

        Raises:
            HTTPException
        """

        if await self.contact_repo.is_contact(
            contact_data.email, contact_data.phonenumber, user
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contact with email - '{contact_data.email}' or phone number - '{contact_data.phonenumber}' already exists.",
            )
        return await self.contact_repo.create_contact(contact_data, user)

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
        Contact list

        Args:
            firstname (str): Contact first name
            lastname (str): Contact last name
            email (str): Contact email
            skip (int): Number of contacts to skip
            limit (int): Maximum number of contacts
            user (User): Contact user

        Returns:
            List of contacts
        """

        return await self.contact_repo.fetch_contacts(
            firstname, lastname, email, skip, limit, user
        )

    async def fetch_contact_by_id(self, contact_id: int, user: User) -> Contact | None:
        """
        Returns contact by ID

        Args:
            contact_id (int): Contact ID
            user (User): Contact user

        Returns:
            Contact
        """

        contact = await self.contact_repo.get_contact_by_id(contact_id, user)
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contact with ID {contact_id} not found.",
            )
        return contact

    async def update_exist_contact(
        self, contact_id: int, contact_data: ContactModel, user: User
    ) -> Contact:
        """
        Update Contact

        Args:
            contact_id (int): Contact ID
            contact_data (ContactModel): ContactModel
            user (User): Contact user

        Returns:
            Updated Contact
        """

        updated_contact = await self.contact_repo.update_contact(
            contact_id, contact_data, user
        )
        if not updated_contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contact with ID {contact_id} not found for update.",
            )
        return updated_contact

    async def delete_contact(self, contact_id: int, user: User) -> Contact:
        """
        Delete contact

        Args:
            contact_id (int): Contact ID
            user (User): Contact user

        Returns:
            Deleted contact
        """

        deletion_success = await self.contact_repo.delete_contact(contact_id, user)
        if not deletion_success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contact with ID {contact_id} not found for deletion.",
            )
        return {"message": f"Contact with ID {contact_id} successfully deleted."}

    async def fetch_upcoming_birthdays(
        self, days_ahead: int, user: User
    ) -> List[Contact]:
        """
        List of upcoming birthdays

        Args:
            days_ahead (int): Number of days in the future
            user (User): User who owns the contacts.

        Returns:
            List of upcoming birthdays
        """

        return await self.contact_repo.fetch_upcoming_birthdays(days_ahead, user)
