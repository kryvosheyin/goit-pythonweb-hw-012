from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.services.auth import get_current_user
from src.database.db import get_db
from src.schemas.contacts import (
    ContactModel,
    ContactResponseModel,
    User,
    MessageResponse,
)
from src.services.contacts import ContactService
from src.utils import constants

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get(
    "/birthdays",
    response_model=list[ContactResponseModel],
    summary="Get upcoming birthdays",
)
async def fetch_birthdays(
    days: int = Query(default=7, ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Get all contacts with upcoming birthdays within the next `days` days.

    Args:
        days (int): Number of days to look ahead for upcoming birthdays. Defaults to 7.
    Returns:
        list[ContactResponseModel]: List of contacts with upcoming birthdays.
    """
    contact_service = ContactService(db)
    return await contact_service.fetch_upcoming_birthdays(days, user)


@router.get("/", response_model=List[ContactResponseModel], summary="Get all contacts")
async def fetch_contacts(
    firstname: str = "",
    lastname: str = "",
    email: str = "",
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Get a list of contacts matching the given filters.

    Args:
        firstname (str): Optional filter by contact firstname. Defaults to "".
        lastname (str): Optional filter by contact lastname. Defaults to "".
        email (str): Optional filter by contact email. Defaults to "".
        skip (int): Number of contacts to skip. Defaults to 0.
        limit (int): Number of contacts to return. Defaults to 100.

    Returns:
        List[ContactResponseModel]: List of contacts matching the given filters.
    """
    contact_service = ContactService(db)
    contacts = await contact_service.fetch_contacts(
        firstname=firstname,
        lastname=lastname,
        email=email,
        skip=skip,
        limit=limit,
        user=user,
    )
    return contacts


@router.get(
    "/{contact_id}", response_model=ContactResponseModel, summary="Get exact contact"
)
async def fetch_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Get an exact contact by contact ID.

    Args:
        contact_id (int): Contact ID to retrieve.

    Returns:
        ContactResponseModel: Contact matching the given contact ID.

    Raises:
        HTTPException: If contact with the given contact ID does not exist.
    """
    contact_service = ContactService(db)
    contact = await contact_service.fetch_contact_by_id(contact_id, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=constants.CONTACT_NOT_FOUND
        )
    return contact


@router.post(
    "/",
    response_model=ContactResponseModel,
    status_code=status.HTTP_201_CREATED,
    summary="Create new contact",
)
async def create_contact(
    body: ContactModel,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Create a new contact.

    Args:
        body (ContactModel): Contact data to be created.

    Returns:
        ContactResponseModel: Created contact.

    Raises:
        HTTPException: If contact with the same email or phone number already exists.
    """
    contact_service = ContactService(db)
    return await contact_service.create_new_contact(body, user)


@router.put(
    "/{contact_id}", response_model=ContactResponseModel, summary="Update exist contact"
)
async def update_contact(
    body: ContactModel,
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Update an existing contact.

    Args:
        body (ContactModel): Contact data to be updated.
        contact_id (int): ID of contact to be updated.

    Returns:
        ContactResponseModel: Updated contact.

    Raises:
        HTTPException: If contact with the given contact ID does not exist.
    """
    contact_service = ContactService(db)
    contact = await contact_service.update_exist_contact(contact_id, body, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=constants.CONTACT_NOT_FOUND
        )
    return contact


@router.delete(
    "/{contact_id}", response_model=MessageResponse, summary="Delete a contact"
)
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Delete an existing contact.

    Args:
        contact_id (int): ID of contact to be deleted.

    Returns:
        MessageResponse: Message indicating whether contact was deleted successfully.

    Raises:
        HTTPException: If contact with the given contact ID does not exist.
    """
    contact_service = ContactService(db)
    deleted_contact = await contact_service.delete_contact(contact_id, user)
    if deleted_contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=constants.CONTACT_NOT_FOUND
        )
    return {"message": f"Contact with ID {contact_id} successfully deleted."}
