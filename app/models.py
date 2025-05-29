"""
Pydantic models for webhook payload validation.

This module defines the data models used for validating incoming webhook payloads
and ensuring type safety throughout the application.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EventWebhookPayload(BaseModel):
    """
    Model for webhook event payload.
    
    This model represents the structure of incoming webhook events
    for resource reservation management.
    """
    
    # Event metadata
    event_type: str = Field(..., alias='eventType', description="Type of the event (e.g., EVENT_START, EVENT_END)")
    timestamp: datetime = Field(..., description="Timestamp when the event occurred")
    event_id: str = Field(..., alias='eventId', description="Unique identifier for the event")

    # User information
    user_id: Optional[str] = Field(None, alias='userId', description="ID of the user associated with the event")
    username: Optional[str] = Field(None, description="Username of the user")
    email: Optional[str] = Field(None, description="Email address of the user")
    ssh_public_key: Optional[str] = Field(None, alias='sshPublicKey', description="SSH public key for resource access")

    # Event details
    event_title: Optional[str] = Field(None, alias='eventTitle', description="Title of the reservation event")
    event_description: Optional[str] = Field(None, alias='eventDescription', description="Description of the event")
    event_start: Optional[datetime] = Field(None, alias='eventStart', description="Start time of the reservation")
    event_end: Optional[datetime] = Field(None, alias='eventEnd', description="End time of the reservation")

    # Resource information
    resource_id: Optional[int] = Field(None, alias='resourceId', description="Unique ID of the resource")
    resource_name: Optional[str] = Field(None, alias='resourceName', description="Name of the resource")
    resource_type: Optional[str] = Field(None, alias='resourceType', description="Type of the resource")
    resource_specs: Optional[str] = Field(None, alias='resourceSpecs', description="Specifications of the resource")
    resource_location: Optional[str] = Field(None, alias='resourceLocation', description="Physical location of the resource")

    # Site information
    site_id: Optional[str] = Field(None, alias='siteId', description="ID of the site where the resource is located")
    site_name: Optional[str] = Field(None, alias='siteName', description="Name of the site")

    class Config:
        """Pydantic model configuration."""
        allow_population_by_field_name = True  # Allows using both Python and alias field names
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "eventType": "EVENT_START",
                "timestamp": "2025-05-29T10:30:00Z",
                "eventId": "evt_123456",
                "userId": "user_789",
                "username": "john.doe",
                "email": "john.doe@example.com",
                "sshPublicKey": "ssh-rsa AAAAB3NzaC1yc2EAAAADA...",
                "eventTitle": "Server Reservation",
                "eventDescription": "Reserved for testing purposes",
                "eventStart": "2025-05-29T10:00:00Z",
                "eventEnd": "2025-05-29T18:00:00Z",
                "resourceId": 42,
                "resourceName": "server-01",
                "resourceType": "bare-metal",
                "resourceSpecs": "16 cores, 64GB RAM, 1TB SSD",
                "resourceLocation": "Rack A1",
                "siteId": "site_001",
                "siteName": "Main Data Center"
            }
        }
