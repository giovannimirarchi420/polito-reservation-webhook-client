# Webhook Payload Examples

## Batch Event Webhook Payload (New Implementation)

When multiple events from the same user are processed simultaneously, a batch payload is sent with the following structure:

### EVENT_START Batch Example
```json
{
  "eventType": "EVENT_START",
  "timestamp": "2025-06-08T14:30:00.000+02:00",
  "eventCount": 3,
  "userId": "keycloak-user-id-123",
  "username": "giovanni.mirarchi",
  "email": "giovanni.mirarchi@example.com",
  "sshPublicKey": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC...",
  "events": [
    {
      "eventId": "101",
      "eventTitle": "Server Maintenance Lab A",
      "eventDescription": "Maintenance work on lab servers",
      "eventStart": "2025-06-08T15:00:00.000+02:00",
      "eventEnd": "2025-06-08T17:00:00.000+02:00",
      "resourceId": 1,
      "resourceName": "Lab Server A1",
      "resourceType": "Server",
      "resourceSpecs": "Intel Xeon E5-2690, 32GB RAM, 1TB SSD",
      "resourceLocation": "Building A, Room 101",
      "siteId": "site-polito-torino",
      "siteName": "Politecnico di Torino"
    },
    {
      "eventId": "102",
      "eventTitle": "Database Testing",
      "eventDescription": "Performance testing on database cluster",
      "eventStart": "2025-06-08T15:30:00.000+02:00",
      "eventEnd": "2025-06-08T18:00:00.000+02:00",
      "resourceId": 2,
      "resourceName": "DB Cluster Node 1",
      "resourceType": "Database",
      "resourceSpecs": "PostgreSQL 14, 64GB RAM, NVMe SSD",
      "resourceLocation": "Building A, Room 102",
      "siteId": "site-polito-torino",
      "siteName": "Politecnico di Torino"
    },
    {
      "eventId": "103",
      "eventTitle": "Network Configuration",
      "eventDescription": "Router configuration update",
      "eventStart": "2025-06-08T16:00:00.000+02:00",
      "eventEnd": "2025-06-08T17:30:00.000+02:00",
      "resourceId": 5,
      "resourceName": "Core Router R1",
      "resourceType": "Network Equipment",
      "resourceSpecs": "Cisco ASR 9000, 48 ports",
      "resourceLocation": "Network Room, Floor 1",
      "siteId": "site-polito-torino",
      "siteName": "Politecnico di Torino"
    }
  ],
  "activeResources": [
    {
      "eventId": "95",
      "eventTitle": "Ongoing Database Maintenance",
      "eventDescription": "Regular maintenance on production database",
      "eventStart": "2025-06-08T13:00:00.000+02:00",
      "eventEnd": "2025-06-08T19:00:00.000+02:00",
      "resourceId": 8,
      "resourceName": "Production DB Server",
      "resourceType": "Database",
      "resourceSpecs": "PostgreSQL 15, 128GB RAM, NVMe SSD",
      "resourceLocation": "Data Center, Rack 3",
      "siteId": "site-polito-torino",
      "siteName": "Politecnico di Torino"
    }
  ]
}
```

### EVENT_END Batch Example
```json
{
  "eventType": "EVENT_END",
  "timestamp": "2025-06-08T18:00:00.000+02:00",
  "eventCount": 2,
  "userId": "keycloak-user-id-456",
  "username": "marco.rossi",
  "email": "marco.rossi@example.com",
  "sshPublicKey": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQD...",
  "events": [
    {
      "eventId": "98",
      "eventTitle": "GPU Computing Task",
      "eventDescription": "Machine learning model training completed",
      "eventStart": "2025-06-08T10:00:00.000+02:00",
      "eventEnd": "2025-06-08T18:00:00.000+02:00",
      "resourceId": 10,
      "resourceName": "GPU Server G1",
      "resourceType": "GPU Server",
      "resourceSpecs": "NVIDIA A100, 80GB VRAM, 128GB System RAM",
      "resourceLocation": "HPC Center, Rack 5",
      "siteId": "site-polito-torino",
      "siteName": "Politecnico di Torino"
    },
    {
      "eventId": "99",
      "eventTitle": "Data Analysis",
      "eventDescription": "Statistical analysis of research data",
      "eventStart": "2025-06-08T12:00:00.000+02:00",
      "eventEnd": "2025-06-08T18:00:00.000+02:00",
      "resourceId": 11,
      "resourceName": "Analysis Workstation W1",
      "resourceType": "Workstation",
      "resourceSpecs": "Intel i9-12900K, 64GB RAM, RTX 3080",
      "resourceLocation": "Research Lab, Room 205",
      "siteId": "site-polito-torino",
      "siteName": "Politecnico di Torino"
    }
  ],
  "activeResources": [
    {
      "eventId": "97",
      "eventTitle": "Continuous Integration Server",
      "eventDescription": "CI/CD pipeline running",
      "eventStart": "2025-06-08T08:00:00.000+02:00",
      "eventEnd": "2025-06-08T20:00:00.000+02:00",
      "resourceId": 15,
      "resourceName": "CI Server Jenkins-1",
      "resourceType": "Server",
      "resourceSpecs": "Intel Xeon E5-2680, 64GB RAM, 2TB SSD",
      "resourceLocation": "DevOps Lab, Rack 2",
      "siteId": "site-polito-torino",
      "siteName": "Politecnico di Torino"
    },
    {
      "eventId": "96",
      "eventTitle": "Development Environment",
      "eventDescription": "Development work in progress",
      "eventStart": "2025-06-08T09:00:00.000+02:00",
      "eventEnd": "2025-06-08T22:00:00.000+02:00",
      "resourceId": 12,
      "resourceName": "Dev Workstation D1",
      "resourceType": "Workstation",
      "resourceSpecs": "AMD Ryzen 9 5950X, 32GB RAM, RTX 3070",
      "resourceLocation": "Development Lab, Room 301",
      "siteId": "site-polito-torino",
      "siteName": "Politecnico di Torino"
    }
  ]
}
```

## Single Event Webhook Payload (Backward Compatibility)

For compatibility with existing implementations, single events are still sent with this format:

### Single EVENT_START Example
```json
{
  "eventType": "EVENT_START",
  "timestamp": "2025-06-08T14:30:00.000+02:00",
  "eventId": "101",
  "userId": "keycloak-user-id-123",
  "username": "giovanni.mirarchi",
  "email": "giovanni.mirarchi@example.com",
  "sshPublicKey": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC...",
  "eventTitle": "Server Maintenance Lab A",
  "eventDescription": "Maintenance work on lab servers",
  "eventStart": "2025-06-08T15:00:00.000+02:00",
  "eventEnd": "2025-06-08T17:00:00.000+02:00",
  "resourceId": 1,
  "resourceName": "Lab Server A1",
  "resourceType": "Server",
  "resourceSpecs": "Intel Xeon E5-2690, 32GB RAM, 1TB SSD",
  "resourceLocation": "Building A, Room 101",
  "siteId": "site-polito-torino",
  "siteName": "Politecnico di Torino"
}
```

## How to Distinguish Between Formats

### Batch Format
- Contains the `eventCount` field (number of events in the batch)
- Contains the `events` array with details of each event
- Contains the `activeResources` array with resources currently in use by the user (optional, can be `null` or empty)
- Does NOT contain direct event fields (`eventId`, `eventTitle`, etc. directly in the root)

### Single Format
- Does NOT contain the `eventCount` field
- Does NOT contain the `events` array
- Does NOT contain the `activeResources` array
- Contains direct event fields (`eventId`, `eventTitle`, etc. directly in the root)

## Suggested Implementation for the Receiver

```javascript
function handleWebhook(payload) {
  if (payload.eventCount && payload.events) {
    // Batch format - handle array of events
    console.log(`Received ${payload.eventCount} events for user ${payload.username}`);
    
    payload.events.forEach(event => {
      console.log(`Event ${event.eventId}: ${event.eventTitle} (${event.eventStart} - ${event.eventEnd})`);
      console.log(`Resource: ${event.resourceName} (${event.resourceType})`);
      // Handle each event...
    });
    
    // Handle currently active resources for the user
    if (payload.activeResources && payload.activeResources.length > 0) {
      console.log(`User ${payload.username} has ${payload.activeResources.length} resources currently in use:`);
      payload.activeResources.forEach(activeResource => {
        console.log(`- ${activeResource.resourceName} (${activeResource.resourceType})`);
        console.log(`  Reservation: ${activeResource.eventTitle} (until ${activeResource.eventEnd})`);
      });
    } else {
      console.log(`User ${payload.username} has no resources currently in use`);
    }
    
    // Common user information for all events
    const userInfo = {
      userId: payload.userId,
      username: payload.username,
      email: payload.email,
      sshPublicKey: payload.sshPublicKey
    };
    
  } else {
    // Single format - handle single event
    console.log(`Received single event ${payload.eventId} for user ${payload.username}`);
    console.log(`Event: ${payload.eventTitle} (${payload.eventStart} - ${payload.eventEnd})`);
    console.log(`Resource: ${payload.resourceName} (${payload.resourceType})`);
    // Handle single event...
  }
}
```

## Important Notes

1. **User Consistency**: All events in a batch always belong to the same user (`userId`)
2. **Timing**: Timestamps are always in ISO 8601 format with timezone
3. **Optional Fields**: Some fields can be `null` if information is not available (e.g., `sshPublicKey`, `siteName`, `activeResources`)
4. **Active Resources**: The `activeResources` field contains all resources that the user currently has in use (events that have started but not yet ended at the time of webhook sending)
5. **HMAC Signature**: The webhook includes an `X-Webhook-Signature` header for authenticity verification
6. **Backward Compatibility**: The system continues to support both formats

## Advantages of Batch Format

1. **Efficiency**: Reduces the number of HTTP calls when multiple events start/end simultaneously
2. **Consistency**: Ensures that all events belong to the same user
3. **User Information**: User information (username, email, SSH key) is retrieved only once for the entire batch
4. **Complete Context**: Includes currently active resources for the user to provide a complete view of the current state
5. **Ease of Management**: Allows for easier batch operation processing (e.g., setting up multiple environments for the same user)

## activeResources Field

The `activeResources` field is a new feature that provides information about resources currently in use by the user at the time of webhook sending. This field is only present in the batch format and can be very useful for various scenarios:

### When activeResources is populated

- **EVENT_START**: Shows all resources that the user already had in use before the start of new events
- **EVENT_END**: Shows all resources that the user continues to have in use after the ended events have finished

### Structure of activeResources

The `activeResources` field is an array of `EventInfo` objects with the same structure as elements in `events`:

```json
{
  "activeResources": [
    {
      "eventId": "95",
      "eventTitle": "Ongoing Database Maintenance",
      "eventDescription": "Regular maintenance on production database",
      "eventStart": "2025-06-08T13:00:00.000+02:00",
      "eventEnd": "2025-06-08T19:00:00.000+02:00",
      "resourceId": 8,
      "resourceName": "Production DB Server",
      "resourceType": "Database",
      "resourceSpecs": "PostgreSQL 15, 128GB RAM, NVMe SSD",
      "resourceLocation": "Data Center, Rack 3",
      "siteId": "site-polito-torino",
      "siteName": "Politecnico di Torino"
    }
  ]
}
```

### Use cases for activeResources

1. **Conflict Management**: Check if a user is already using similar or related resources
2. **Monitoring**: Monitor overall resource usage per user
3. **Automation**: Automatically configure environments that depend on resources already in use
4. **Reporting**: Generate reports on simultaneous resource usage
5. **Notifications**: Notify administrators when a user exceeds an active resource threshold

### Example management logic

```javascript
function processWebhook(payload) {
  if (payload.eventType === 'EVENT_START') {
    console.log(`User ${payload.username} is starting ${payload.eventCount} new events`);
    
    if (payload.activeResources && payload.activeResources.length > 0) {
      console.log(`User already had ${payload.activeResources.length} active resources:`);
      payload.activeResources.forEach(resource => {
        console.log(`- ${resource.resourceName} (until ${resource.eventEnd})`);
      });
      
      // Check if user has too many active resources
      const totalActive = payload.activeResources.length + payload.eventCount;
      if (totalActive > 5) {
        console.warn(`WARNING: User ${payload.username} now has ${totalActive} active resources!`);
      }
    }
  }
}
```

### Technical notes

- The `activeResources` field can be `null` or an empty array if the user has no currently active resources
- Events in `activeResources` are always different from those in `events` (no duplicates)
- The search for active resources is performed at the time of webhook sending using the current timestamp
- If there's an error retrieving active resources, the field is set to `null` and the webhook is still sent
