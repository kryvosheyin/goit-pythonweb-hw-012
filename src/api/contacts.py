from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.database.db import get_db
from src.schemas.contacts import ContactModel, ContactResponseModel
from src.services.contacts import ContactService

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get(
    "/birthdays",
    response_model=list[ContactResponseModel],
    summary="Get upcoming birthdays",
)
async def fetch_birthdays(
    days: int = Query(default=7, ge=1), db: AsyncSession = Depends(get_db)
):
    contact_service = ContactService(db)
    return await contact_service.fetch_upcoming_birthdays(days)


@router.get("/", response_model=List[ContactResponseModel], summary="Get all contacts")
async def fetch_contacts(
    firstname: str = "",
    lastname: str = "",
    email: str = "",
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    contact_service = ContactService(db)
    contacts = await contact_service.fetch_contacts(
        firstname, lastname, email, skip, limit
    )
    return contacts


@router.get(
    "/{contact_id}", response_model=ContactResponseModel, summary="Get exact contact"
)
async def fetch_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    contact_service = ContactService(db)
    contact = await contact_service.fetch_contact_by_id(contact_id)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact does not exist."
        )
    return contact


@router.post(
    "/",
    response_model=ContactResponseModel,
    status_code=status.HTTP_201_CREATED,
    summary="Create new contact",
)
async def create_contact(body: ContactModel, db: AsyncSession = Depends(get_db)):
    contact_service = ContactService(db)
    return await contact_service.create_new_contact(body)


@router.put(
    "/{contact_id}", response_model=ContactResponseModel, summary="Update exist contact"
)
async def update_contact(
    body: ContactModel, contact_id: int, db: AsyncSession = Depends(get_db)
):
    contact_service = ContactService(db)
    contact = await contact_service.update_exist_contact(contact_id, body)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact does not exist."
        )
    return contact


@router.delete(
    "/{contact_id}", response_model=ContactResponseModel, summary="Delete exist contact"
)
async def delete_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    contact_service = ContactService(db)
    contact = await contact_service.delete_contact(contact_id)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact does not exist."
        )
    return contact