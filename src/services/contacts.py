from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.database.models import Contact, User
from src.repository.contacts import ContactsRepository
from src.schemas.contacts import ContactModel


class ContactService:
    """
    Handles business logic related to contacts.
    """

    def __init__(self, db_session: AsyncSession):

        self.contact_repo = ContactsRepository(db_session)

    async def create_new_contact(
        self, contact_data: ContactModel, user: User
    ) -> Contact:
        """
        Creates a new contact for the given user.

        Args:
            contact_data (ContactModel): The contact data to be created.
            user (User): The user who is creating the contact.

        Returns:
            Contact: The created contact.

        Raises:
            HTTPException: If a contact with the same email or phone number already exists.
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
        Fetches a list of contacts based on the given filters.

        Args:
            user (User): The user whose contacts are to be fetched.
            firstname (str, optional): Optional filter by contact firstname. Defaults to None.
            lastname (str, optional): Optional filter by contact lastname. Defaults to None.
            email (str, optional): Optional filter by contact email. Defaults to None.
            skip (int, optional): Number of contacts to skip. Defaults to 0.
            limit (int, optional): Number of contacts to return. Defaults to 10.

        Returns:
            List[Contact]: List of contacts matching the given filters.
        """
        return await self.contact_repo.fetch_contacts(
            firstname=firstname,
            lastname=lastname,
            email=email,
            skip=skip,
            limit=limit,
            user=user,
        )

    async def fetch_contact_by_id(self, contact_id: int, user: User) -> Contact | None:
        """
        Fetches a contact by contact ID.

        Args:
            contact_id (int): The contact ID to fetch.
            user (User): The user whose contact is to be fetched.

        Returns:
            Contact | None: The fetched contact if found, otherwise None.

        Raises:
            HTTPException: If contact with the given contact ID does not exist.
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
        Updates a contact by contact ID.

        Args:
            contact_id (int): The contact ID to update.
            contact_data (ContactModel): The contact data to be updated.
            user (User): The user who is updating the contact.

        Returns:
            Contact: The updated contact if found, otherwise None.

        Raises:
            HTTPException: If contact with the given contact ID does not exist.
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
        Deletes a contact by contact ID.

        Args:
            contact_id (int): The contact ID to delete.
            user (User): The user who is deleting the contact.

        Returns:
            Contact: The deleted contact if found, otherwise None.

        Raises:
            HTTPException: If contact with the given contact ID does not exist.
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

        return await self.contact_repo.fetch_upcoming_birthdays(days_ahead, user)
