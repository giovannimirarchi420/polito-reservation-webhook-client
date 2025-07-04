"""
Pydantic models for webhook payload validation.

This module defines the data models used for validating incoming webhook payloads
and ensuring type safety throughout the application.
"""
from datetime import datetime
from typing import Optional, List  # Union removed

from pydantic import BaseModel, Field


class Event(BaseModel):
    """Model for individual event details within a batch."""
    event_id: str = Field(..., alias='eventId', description="Unique identifier for the event")
    event_title: Optional[str] = Field(None, alias='eventTitle', description="Title of the reservation event")
    event_description: Optional[str] = Field(None, alias='eventDescription', description="Description of the event")
    event_start: datetime = Field(..., alias='eventStart', description="Start time of the event")
    event_end: datetime = Field(..., alias='eventEnd', description="End time of the event")
    resource_id: int = Field(..., alias='resourceId', description="Identifier of the resource")
    resource_name: str = Field(..., alias='resourceName', description="Name of the resource")
    resource_type: str = Field(..., alias='resourceType', description="Type of the resource")
    resource_specs: Optional[str] = Field(None, alias='resourceSpecs', description="Specifications of the resource")
    resource_location: Optional[str] = Field(None, alias='resourceLocation', description="Location of the resource")
    site_id: Optional[str] = Field(None, alias='siteId', description="Identifier of the site")
    site_name: Optional[str] = Field(None, alias='siteName', description="Name of the site")


class WebhookPayload(BaseModel):
    """
    Model for webhook event payload.
    It always expects a list of events, even for a single event.
    """
    webhook_id: str = Field(..., alias='webhookId', description="Unique identifier for the webhook call")
    event_type: str = Field(..., alias='eventType', description="Type of the event (e.g., EVENT_START, EVENT_END)")
    timestamp: datetime = Field(..., description="Timestamp when the batch event occurred")
    event_count: int = Field(..., alias='eventCount', description="Number of events in the batch (will be 1 for a single event)")
    user_id: Optional[str] = Field(None, alias='userId', description="ID of the user associated with the events")
    username: Optional[str] = Field(None, description="Username of the user")
    email: Optional[str] = Field(None, description="Email address of the user")
    ssh_public_key: Optional[str] = Field(None, alias='sshPublicKey', description="SSH public key for resource access")
    events: List[Event] = Field(..., description="List of individual events. Will contain one item for a single logical event.")
    active_resources: Optional[List[Event]] = Field(None, alias='activeResources', description="List of resources currently in use by the user (events that have started but not yet ended at the time of webhook sending)")


class EventResourceInfo(BaseModel):
    """Model for resource information within EVENT_DELETED data."""
    name: str = Field(..., description="Name of the resource to be deprovisioned")


class EventData(BaseModel):
    """Model for the 'data' field in an EVENT_DELETED payload."""
    id: int = Field(..., description="Unique identifier for the deletion event data")
    start: datetime = Field(..., description="Original start time of the reservation")
    end: datetime = Field(..., description="Original end time of the reservation")
    resource: EventResourceInfo = Field(..., description="Details of the resource associated with the event")
    keycloak_id: Optional[str] = Field(None, alias='keycloakId', description="Keycloak ID of the user")


class EventWebhookPayload(BaseModel):
    """Model for EVENT_DELETED webhook payload."""
    event_type: str = Field(..., alias='eventType', description="Type of the event, should be EVENT_DELETED")
    timestamp: datetime = Field(..., description="Timestamp when the event occurred")
    webhook_id: str = Field(..., alias='webhookId', description="Unique identifier for the webhook call")
    data: EventData = Field(..., description="Detailed data for the EVENT_DELETED event")
