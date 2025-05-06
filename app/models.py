from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class EventWebhookPayload(BaseModel):
    event_type: str = Field(..., alias='eventType')
    timestamp: datetime
    event_id: str = Field(..., alias='eventId')

    # User Information
    user_id: Optional[str] = Field(None, alias='userId')
    username: Optional[str] = None
    email: Optional[str] = None
    ssh_public_key: Optional[str] = Field(None, alias='sshPublicKey')

    # Event Information
    event_title: Optional[str] = Field(None, alias='eventTitle')
    event_description: Optional[str] = Field(None, alias='eventDescription')
    event_start: Optional[datetime] = Field(None, alias='eventStart')
    event_end: Optional[datetime] = Field(None, alias='eventEnd')

    # Resource Information
    resource_id: Optional[int] = Field(None, alias='resourceId')
    resource_name: Optional[str] = Field(None, alias='resourceName')
    resource_type: Optional[str] = Field(None, alias='resourceType')
    resource_specs: Optional[str] = Field(None, alias='resourceSpecs')
    resource_location: Optional[str] = Field(None, alias='resourceLocation')

    # Site Information
    site_id: Optional[str] = Field(None, alias='siteId')
    site_name: Optional[str] = Field(None, alias='siteName')

    class Config:
        allow_population_by_field_name = True # Allows using Java field names (e.g., eventType)
        # orm_mode = True # If you plan to use this with an ORM
