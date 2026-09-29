# ParentGuide — Complete Project Specification

> **Purpose:** This document is the single source of truth for building ParentGuide. It is intentionally detailed so that an LLM, developer, or development team can use it to understand the product, architecture, implementation order, milestones, and technical requirements.

---

# 1. Project Overview

**ParentGuide** is a family safety and management platform that helps families stay connected, organized, and informed.

The platform allows users to:

- Create or join private families.
- Assign family roles such as Father, Mother, Child, Guardian, etc.
- Define permissions for each family member.
- Share and monitor live locations.
- View location history.
- Create geographic safe zones/geofences.
- Receive alerts when a member enters or leaves a geofence.
- Trigger emergency/SOS alerts.
- Track a member's live location during an emergency.
- Communicate through private family chat.
- Create reminders and scheduled notifications.
- Manage family tasks and events.
- Perform safety check-ins.
- Manage emergency contacts.
- Monitor device/location-sharing status.
- Eventually support school, transportation, expenses, rewards, travel, AI assistance, and other family-management modules.

ParentGuide is **not simply a location tracker**. It is intended to become a complete family safety and coordination platform.

---

# 2. Primary Product Goals

## 2.1 Safety

The most important objective is to allow authorized family members to know when something important happens.

Examples:

- Child leaves school geofence.
- Child arrives home.
- Child has not completed a safety check-in.
- Child triggers SOS.
- Child's device becomes unavailable.
- Location sharing is disabled.
- Emergency tracking is active.

## 2.2 Communication

Families should have a private communication environment:

- Family group chat.
- Messages.
- Location sharing.
- Announcements.
- Emergency communication.

## 2.3 Organization

Families should be able to manage:

- Reminders.
- Calendar events.
- Tasks.
- Chores.
- Check-ins.
- Shared lists.

## 2.4 Extensibility

The architecture must allow future modules without requiring a complete rewrite.

---

# 3. Target Users

## 3.1 Parent / Guardian

Typical capabilities:

- Create family.
- Invite members.
- Manage family members.
- Assign roles.
- View authorized children's locations.
- Create geofences.
- Receive safety alerts.
- Receive SOS alerts.
- Create reminders.
- Create tasks.
- Participate in family chat.
- View emergency history.
- Configure family safety settings.

## 3.2 Child

Typical capabilities:

- Join family.
- Share location according to configured permissions.
- View authorized family members.
- Receive reminders.
- Participate in family chat.
- Complete safety check-ins.
- Complete assigned tasks.
- Trigger SOS.

## 3.3 Administrator

An optional future web/admin role.

Capabilities may include:

- User management.
- System monitoring.
- Abuse reports.
- Audit logs.
- Platform configuration.
- Support tools.

The administrator must not automatically have access to private family location data unless a clearly defined legal/support workflow requires it.

---

# 4. Core Product Modules

The initial product should be divided into these modules:

1. Authentication
2. User Profile
3. Family Management
4. Roles & Permissions
5. Location Sharing
6. Live Location
7. Location History
8. Places
9. Geofencing
10. Push Notifications
11. Emergency / SOS
12. Emergency Live Tracking
13. Family Chat
14. Reminders
15. Safety Check-ins
16. Family Tasks / Chores
17. Family Calendar
18. Emergency Contacts
19. Device Management
20. Privacy & Security
21. Audit / Activity Logs

Future modules:

22. School Management
23. Transportation
24. Allowance / Expenses
25. Rewards
26. Family Shopping List
27. Family Document Vault
28. Travel Mode
29. Family Goals
30. AI Family Assistant
31. Smart Safety Insights
32. Advanced Analytics

---

# 5. Recommended Technology Stack

## 5.1 General

Use **TypeScript** across frontend and backend where practical.

## 5.2 Mobile

Recommended:

- React Native
- TypeScript
- React Navigation
- TanStack Query
- Zustand
- Axios
- Socket.IO Client
- Firebase Messaging
- Secure storage
- Background location solution
- Map SDK

The mobile app is the primary client because location tracking, push notifications, and emergency functionality are mobile-centric.

## 5.3 Web

Recommended:

- React
- TypeScript
- Vite
- React Router
- TanStack Query
- Zustand
- Tailwind CSS

The web application can initially focus on administration and family management.

## 5.4 Backend

- Node.js
- Express.js
- TypeScript
- Mongoose
- Zod
- JWT
- Refresh tokens
- Socket.IO
- Firebase Admin SDK

## 5.5 Database

- MongoDB
- MongoDB Atlas in production
- Mongoose ODM
- MongoDB geospatial indexes

## 5.6 Cache / Real-Time Infrastructure

- Redis
- BullMQ

Redis is used for:

- Latest location state.
- Temporary state.
- Caching.
- Rate limiting.
- Presence.
- Job infrastructure.

MongoDB remains the persistent source of truth.

## 5.7 Real-Time

- Socket.IO

Used for:

- Live location.
- Chat.
- Emergency tracking.
- Presence.
- Real-time family events.

## 5.8 Push Notifications

- Firebase Cloud Messaging
- Firebase Admin SDK
- APNs through the supported iOS notification infrastructure

## 5.9 Maps / Geolocation

Choose one after evaluating pricing and required functionality:

- Google Maps Platform
- Mapbox

Required capabilities:

- Interactive map.
- Markers.
- Geocoding.
- Reverse geocoding.
- Directions where required.
- Distance calculations.
- Location visualization.

## 5.10 File Storage

Possible options:

- AWS S3
- Cloudinary

Use object storage instead of storing large files directly in MongoDB.

## 5.11 Background Jobs

- BullMQ
- Redis

Used for:

- Scheduled reminders.
- Notifications.
- Cleanup.
- Location-history processing.
- Geofence processing where appropriate.
- Recurring jobs.

## 5.12 Security / Validation

- Zod
- Helmet
- CORS
- Rate limiting
- Password hashing with Argon2id or bcrypt
- Secure HTTP-only cookies where appropriate
- JWT access tokens
- Refresh token rotation

## 5.13 Monitoring

Recommended:

- Sentry
- Pino structured logging

Optional later:

- Prometheus
- Grafana

## 5.14 DevOps

- Git
- GitHub
- GitHub Actions
- Docker
- Docker Compose

---

# 6. High-Level Architecture

```text
                    ParentGuide
                         |
          +--------------+--------------+
          |                             |
     Mobile App                     Web App
   React Native                    React
   TypeScript                      TypeScript
          |                             |
          +-------------+---------------+
                        |
                 REST API / HTTPS
                        |
               Node.js + Express
                        |
       +----------------+----------------+
       |                |                |
    MongoDB           Redis          Socket.IO
       |                |                |
 Persistent         Cache /         Real-time
 Data               Jobs            Events
                        |
                     BullMQ
                        |
                Background Workers
                        |
              +---------+---------+
              |                   |
        Notification         Scheduled Jobs
          Service
              |
             FCM
              |
       Android / iOS

External Services:
- Maps provider
- Object storage
- Sentry
```

---

# 7. Architectural Principles

1. Use modular architecture.
2. Keep business logic out of controllers.
3. Validate all external input.
4. Enforce authorization on the server.
5. Never trust client-side role/permission claims.
6. Treat location as sensitive data.
7. Store only the location data that the product actually needs.
8. Use Redis for transient high-frequency state.
9. Use MongoDB for persistent data.
10. Use Socket.IO for real-time delivery.
11. Use push notifications for background alerts.
12. Make all important operations auditable.
13. Design mobile background location separately from normal foreground location.
14. Build with Android and iOS restrictions in mind.
15. Do not expose unrestricted family data to AI services.
16. Keep modules independently testable.

---

# 8. Repository Structure

Recommended monorepo:

```text
parentguide/
│
├── apps/
│   ├── mobile/
│   │   ├── src/
│   │   │   ├── features/
│   │   │   ├── navigation/
│   │   │   ├── components/
│   │   │   ├── services/
│   │   │   ├── store/
│   │   │   ├── hooks/
│   │   │   ├── utils/
│   │   │   └── config/
│   │   └── ...
│   │
│   ├── web/
│   │   ├── src/
│   │   │   ├── features/
│   │   │   ├── pages/
│   │   │   ├── components/
│   │   │   ├── services/
│   │   │   ├── store/
│   │   │   └── ...
│   │   └── ...
│   │
│   └── api/
│       ├── src/
│       │   ├── modules/
│       │   ├── middleware/
│       │   ├── sockets/
│       │   ├── jobs/
│       │   ├── config/
│       │   ├── utils/
│       │   ├── app.ts
│       │   └── server.ts
│       └── ...
│
├── packages/
│   ├── shared/
│   ├── types/
│   ├── validation/
│   └── config/
│
├── infrastructure/
│   ├── docker/
│   └── ...
│
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── database/
│   └── decisions/
│
├── .github/
│   └── workflows/
│
├── docker-compose.yml
├── package.json
└── README.md
```

---

# 9. Domain Model

## 9.1 User

```text
User
- id
- firstName
- lastName
- email
- phone
- passwordHash
- profileImage
- dateOfBirth (if product requires it)
- status
- emailVerified
- phoneVerified
- createdAt
- updatedAt
```

Do not expose sensitive fields through normal API responses.

## 9.2 Family

```text
Family
- id
- name
- createdBy
- image
- status
- createdAt
- updatedAt
```

## 9.3 FamilyMember

Use a separate membership entity instead of embedding everything in Family.

```text
FamilyMember
- id
- familyId
- userId
- role
- permissions
- status
- invitedBy
- joinedAt
- createdAt
- updatedAt
```

Possible roles:

```text
OWNER
PARENT
GUARDIAN
CHILD
MEMBER
```

Roles are product labels. Authorization should ultimately use explicit permissions.

## 9.4 Invitation

```text
Invitation
- id
- familyId
- inviterId
- email or phone
- role
- tokenHash
- expiresAt
- status
- createdAt
```

Never store raw invitation secrets if avoidable.

## 9.5 Device

```text
Device
- id
- userId
- platform
- pushToken
- appVersion
- deviceName
- locationPermissionStatus
- notificationPermissionStatus
- lastSeenAt
- batteryLevel
- isActive
- createdAt
- updatedAt
```

## 9.6 Location

Persistent location history:

```text
Location
- id
- userId
- familyId
- coordinates
- accuracy
- altitude
- speed
- heading
- source
- timestamp
```

Use GeoJSON:

```json
{
  "type": "Point",
  "coordinates": [longitude, latitude]
}
```

Create the appropriate `2dsphere` index.

## 9.7 LatestLocation

Latest location should preferably be represented in Redis for high-frequency access.

Conceptually:

```text
latest-location:{userId}
```

Value:

```json
{
  "latitude": 0,
  "longitude": 0,
  "accuracy": 10,
  "timestamp": "..."
}
```

## 9.8 Place

```text
Place
- id
- familyId
- name
- type
- coordinates
- address
- createdBy
- createdAt
```

Types:

```text
HOME
SCHOOL
WORK
OTHER
```

## 9.9 Geofence

```text
Geofence
- id
- familyId
- name
- center
- radiusMeters
- assignedUserIds
- enabled
- notifyOnEntry
- notifyOnExit
- createdBy
- createdAt
- updatedAt
```

Center should use GeoJSON Point.

## 9.10 GeofenceEvent

```text
GeofenceEvent
- id
- geofenceId
- userId
- type
- location
- timestamp
```

Types:

```text
ENTER
EXIT
```

Deduplicate events to prevent notification spam.

## 9.11 Emergency

```text
Emergency
- id
- familyId
- triggeredBy
- type
- status
- initialLocation
- startedAt
- resolvedAt
- resolvedBy
```

Statuses:

```text
ACTIVE
ACKNOWLEDGED
RESOLVED
CANCELLED
```

## 9.12 EmergencyLocation

For active emergency tracking:

```text
EmergencyLocation
- emergencyId
- userId
- location
- timestamp
```

High-frequency emergency tracking should be designed carefully to control cost and storage.

## 9.13 Message

```text
Message
- id
- familyId
- senderId
- text
- attachments
- replyTo
- createdAt
- editedAt
- deletedAt
```

## 9.14 Notification

```text
Notification
- id
- userId
- familyId
- type
- title
- body
- data
- readAt
- createdAt
```

## 9.15 Reminder

```text
Reminder
- id
- familyId
- createdBy
- assignedTo
- title
- description
- scheduledAt
- recurrence
- status
- createdAt
```

## 9.16 SafetyCheckIn

```text
SafetyCheckIn
- id
- familyId
- createdBy
- assignedTo
- title
- deadline
- status
- respondedAt
- responseLocation
- createdAt
```

## 9.17 Task

```text
Task
- id
- familyId
- createdBy
- assignedTo
- title
- description
- dueAt
- status
- completedAt
- points
```

## 9.18 CalendarEvent

```text
CalendarEvent
- id
- familyId
- createdBy
- title
- description
- startAt
- endAt
- location
- participantIds
- reminderSettings
```

## 9.19 EmergencyContact

```text
EmergencyContact
- id
- userId or familyId
- name
- relationship
- phone
- priority
```

## 9.20 AuditLog

```text
AuditLog
- id
- actorId
- familyId
- action
- targetType
- targetId
- metadata
- timestamp
```

Never log sensitive secrets or tokens.

---

# 10. Roles and Permissions

Recommended permission model:

```text
FAMILY_VIEW
FAMILY_MANAGE
MEMBER_INVITE
MEMBER_MANAGE
LOCATION_VIEW
LOCATION_SHARE
LOCATION_HISTORY_VIEW
GEOFENCE_VIEW
GEOFENCE_MANAGE
EMERGENCY_VIEW
EMERGENCY_TRIGGER
EMERGENCY_MANAGE
CHAT_VIEW
CHAT_SEND
REMINDER_CREATE
REMINDER_MANAGE
TASK_CREATE
TASK_MANAGE
CALENDAR_MANAGE
DEVICE_VIEW
PRIVACY_MANAGE
```

Do not implement authorization using only frontend route guards.

Every protected backend endpoint and Socket.IO event must verify:

1. Authenticated user.
2. Family membership.
3. Required permission.
4. Target member relationship.
5. Resource ownership where applicable.

---

# 11. Authentication Flow

## Registration

```text
Register
  ↓
Validate input
  ↓
Create user
  ↓
Hash password
  ↓
Create verification request
  ↓
Verify account
  ↓
Login
```

## Login

```text
Credentials
  ↓
Validate
  ↓
Check password
  ↓
Issue short-lived access token
  ↓
Issue refresh token
```

## Refresh

```text
Refresh token
  ↓
Validate
  ↓
Rotate refresh token
  ↓
Issue new access token
```

## Logout

Invalidate/revoke refresh token or token family.

---

# 12. Family Creation Flow

```text
User registers
      ↓
Create family
      ↓
Creator becomes OWNER
      ↓
Invite family members
      ↓
Member accepts
      ↓
FamilyMember created
      ↓
Role + permissions applied
```

---

# 13. Location Architecture

Location is one of the most important systems in ParentGuide.

## Normal Tracking

```text
Mobile GPS
   ↓
Permission check
   ↓
Location service
   ↓
Validate update
   ↓
Node.js
   ↓
Redis latest location
   ↓
Socket.IO family room
   ↓
Authorized parent clients
```

Persistent location history should be sampled rather than blindly storing every GPS event.

## Important location fields

```text
latitude
longitude
accuracy
timestamp
speed
heading
source
```

## Location update rules

The backend should reject:

- Invalid coordinates.
- Impossible timestamps.
- Unauthenticated users.
- Unauthorized family updates.
- Excessively frequent updates.
- Suspicious payloads.

Do not assume client timestamps are trustworthy.

---

# 14. Background Location

Background location must be treated as a mobile-specific subsystem.

Requirements:

- Explicit permission.
- Clear user-facing explanation.
- Android background-location requirements.
- iOS background-location requirements.
- Battery-aware updates.
- Offline queueing.
- Retry handling.
- App restart handling.
- Permission-change detection.
- Location-sharing status.

The backend must not assume that a child device can always provide continuous location.

The UI should distinguish:

```text
LIVE
RECENT
OFFLINE
PERMISSION_DISABLED
UNKNOWN
```

---

# 15. Geofencing

A parent creates:

```text
School
Center: latitude/longitude
Radius: 300m
Assigned: Child A
Entry alerts: ON
Exit alerts: ON
```

When a location update arrives:

```text
Location
  ↓
Identify relevant geofences
  ↓
Calculate membership
  ↓
Compare previous state
  ↓
State changed?
  ├── No → Ignore
  └── Yes
       ↓
Create GeofenceEvent
       ↓
Create Notification
       ↓
Send Push
       ↓
Send Socket.IO event
```

Important:

Do not send an alert every time the GPS fluctuates around the boundary.

Use:

- State tracking.
- Accuracy consideration.
- Debouncing.
- Hysteresis where appropriate.
- Event deduplication.

---

# 16. SOS / Emergency Flow

```text
Child presses SOS
       ↓
Client confirms/starts emergency
       ↓
Backend authenticates request
       ↓
Create Emergency
       ↓
Set status = ACTIVE
       ↓
Find authorized guardians
       ↓
Send push notification
       ↓
Emit Socket.IO emergency event
       ↓
Start emergency location stream
       ↓
Parents view live location
       ↓
Parent acknowledges
       ↓
Emergency resolved
```

The emergency system should be optimized for reliability.

It should not depend exclusively on Socket.IO because a backgrounded parent application may not maintain a socket connection.

Use:

```text
Socket.IO + Push Notification
```

together.

---

# 17. Family Chat Architecture

Use Socket.IO for real-time delivery and MongoDB for persistence.

```text
Sender
  ↓
Socket.IO
  ↓
Validate membership
  ↓
Persist message
  ↓
Broadcast family event
  ↓
Recipients
```

If recipients are offline:

```text
Message persisted
  ↓
Push notification
```

Required future features:

- Text.
- Image.
- Location.
- Reply.
- Reactions.
- Edit.
- Delete.
- Read status.
- Pinned messages.

---

# 18. Notification Architecture

Notification types:

```text
EMERGENCY
GEOFENCE_ENTER
GEOFENCE_EXIT
REMINDER
CHECK_IN
CHAT_MESSAGE
FAMILY_INVITATION
TASK_ASSIGNED
TASK_DUE
DEVICE_OFFLINE
LOW_BATTERY
LOCATION_DISABLED
```

Flow:

```text
Domain Event
    ↓
Notification Service
    ↓
Create Notification
    ↓
Find user devices
    ↓
Send FCM
    ↓
Record delivery attempt
```

Notifications must be idempotent where possible.

---

# 19. Reminder Architecture

```text
Create reminder
      ↓
Validate
      ↓
Store MongoDB
      ↓
Schedule BullMQ job
      ↓
Job becomes due
      ↓
Notification service
      ↓
FCM
```

Recurring reminders should generate future jobs safely and avoid duplicate scheduling.

---

# 20. Safety Check-In

Example:

Parent creates:

```text
"Let me know when you reach school."

Deadline: 8:30 AM
Assigned: Child
```

Flow:

```text
Reminder
   ↓
Child receives notification
   ↓
Child taps "I'm Safe"
   ↓
Backend records response
   ↓
Parent receives confirmation
```

If deadline passes:

```text
No response
   ↓
Create overdue event
   ↓
Notify authorized guardian
```

---

# 21. Family Chat Socket Events

Recommended initial events:

```text
family:join
family:leave

message:send
message:new
message:read
message:typing

location:update
location:new

emergency:created
emergency:acknowledged
emergency:resolved
emergency:location

presence:update

notification:new
```

Every event must perform server-side authorization.

---

# 22. REST API Design

Use versioning:

```text
/api/v1
```

## Auth

```text
POST   /auth/register
POST   /auth/login
POST   /auth/refresh
POST   /auth/logout
POST   /auth/verify
POST   /auth/forgot-password
POST   /auth/reset-password
```

## Users

```text
GET    /users/me
PATCH  /users/me
PATCH  /users/me/password
```

## Families

```text
POST   /families
GET    /families
GET    /families/:familyId
PATCH  /families/:familyId
DELETE /families/:familyId
```

## Members

```text
GET    /families/:familyId/members
PATCH  /families/:familyId/members/:memberId
DELETE /families/:familyId/members/:memberId
```

## Invitations

```text
POST   /families/:familyId/invitations
GET    /invitations
POST   /invitations/:id/accept
POST   /invitations/:id/reject
```

## Locations

```text
POST   /families/:familyId/location
GET    /families/:familyId/members/:memberId/location
GET    /families/:familyId/members/:memberId/location-history
```

## Places

```text
POST   /families/:familyId/places
GET    /families/:familyId/places
PATCH  /families/:familyId/places/:placeId
DELETE /families/:familyId/places/:placeId
```

## Geofences

```text
POST   /families/:familyId/geofences
GET    /families/:familyId/geofences
PATCH  /families/:familyId/geofences/:id
DELETE /families/:familyId/geofences/:id
```

## Emergency

```text
POST   /families/:familyId/emergencies
GET    /families/:familyId/emergencies
GET    /families/:familyId/emergencies/:id
POST   /families/:familyId/emergencies/:id/acknowledge
POST   /families/:familyId/emergencies/:id/resolve
```

## Chat

```text
GET    /families/:familyId/messages
POST   /families/:familyId/messages
```

Real-time delivery should use Socket.IO.

## Notifications

```text
GET    /notifications
PATCH  /notifications/:id/read
PATCH  /notifications/read-all
```

## Reminders

```text
POST   /families/:familyId/reminders
GET    /families/:familyId/reminders
PATCH  /families/:familyId/reminders/:id
DELETE /families/:familyId/reminders/:id
```

## Check-ins

```text
POST   /families/:familyId/check-ins
GET    /families/:familyId/check-ins
POST   /families/:familyId/check-ins/:id/respond
```

## Tasks

```text
POST   /families/:familyId/tasks
GET    /families/:familyId/tasks
PATCH  /families/:familyId/tasks/:id
POST   /families/:familyId/tasks/:id/complete
DELETE /families/:familyId/tasks/:id
```

---

# 23. Mobile Application Screens

## Authentication

1. Splash
2. Welcome
3. Login
4. Register
5. Verification
6. Forgot Password
7. Reset Password

## Family Onboarding

8. Create Family
9. Join Family
10. Invite Members
11. Family Setup
12. Role Selection
13. Permission Setup

## Main

14. Home Dashboard
15. Family Map
16. Member List
17. Member Details
18. Location Details
19. Location History

## Safety

20. Safety Center
21. Geofences
22. Create Geofence
23. Geofence Details
24. Emergency Contacts
25. SOS
26. Emergency Active
27. Emergency History
28. Safety Check-ins

## Communication

29. Family Chat
30. Chat Details
31. Media/Location Sharing

## Organization

32. Reminders
33. Create Reminder
34. Calendar
35. Tasks
36. Create Task
37. Family Shopping List

## Account

38. Profile
39. Settings
40. Privacy
41. Location Permissions
42. Notification Settings
43. Devices
44. Family Settings

---

# 24. Web Application Screens

The web app should initially focus on management and monitoring.

```text
Login
Dashboard
Families
Family Details
Members
Live Location
Location History
Geofences
Emergencies
Notifications
Chat
Reminders
Tasks
Calendar
Settings
Audit Logs
```

Future admin portal:

```text
Admin Dashboard
Users
Families
Reports
Support
System Health
Audit Logs
```

---

# 25. Home Dashboard Requirements

The main dashboard should show:

- Family name.
- Family member status.
- Map.
- Current authorized member locations.
- Last update time.
- Active alerts.
- Active emergencies.
- Today's reminders.
- Today's events.
- Pending check-ins.
- Tasks.
- Recent family messages.

Avoid overwhelming the user. Safety-critical information should have visual priority.

---

# 26. Privacy Requirements

Location is sensitive personal data.

Implement:

- Explicit location-sharing consent.
- Clear explanation of location collection.
- Role-based visibility.
- Ability to disable sharing where legally/product-appropriate.
- Location history retention policy.
- Data deletion workflow.
- Account deletion.
- Family membership removal.
- Device/session revocation.
- Audit logging for sensitive actions.

Do not expose a user's exact location to every family member by default.

---

# 27. Security Requirements

## Authentication

- Strong password hashing.
- Short-lived access tokens.
- Refresh token rotation.
- Secure token storage.
- Session revocation.
- Optional MFA.

## API

- HTTPS.
- Helmet.
- CORS configuration.
- Rate limiting.
- Input validation.
- Output sanitization.
- Consistent error handling.
- Authorization middleware.

## Database

- Least-privilege database credentials.
- Encrypted connections.
- Backups.
- Appropriate indexes.
- No secrets committed to Git.

## Secrets

Use environment variables / secret management.

Never commit:

```text
JWT secrets
Database credentials
Firebase private keys
Cloud credentials
API secrets
```

---

# 28. Environment Variables

Example:

```text
NODE_ENV=
PORT=

MONGODB_URI=
REDIS_URL=

JWT_ACCESS_SECRET=
JWT_REFRESH_SECRET=
JWT_ACCESS_EXPIRES_IN=
JWT_REFRESH_EXPIRES_IN=

FIREBASE_PROJECT_ID=
FIREBASE_CLIENT_EMAIL=
FIREBASE_PRIVATE_KEY=

MAPS_API_KEY=

S3_BUCKET=
S3_REGION=
S3_ACCESS_KEY=
S3_SECRET_KEY=

SENTRY_DSN=
```

Use `.env.example`, never commit `.env`.

---

# 29. Testing Strategy

## Backend Unit Tests

Test:

- Authentication.
- Permission checks.
- Geofence calculations.
- Notification creation.
- Reminder scheduling.
- Emergency state transitions.
- Validation.

## Integration Tests

Test:

```text
Register → Login
Create family → Invite → Join
Share location → Parent receives
Create geofence → Exit → Notification
Trigger SOS → Parent receives alert
Create reminder → Job executes
Send message → Recipient receives
```

## Frontend Tests

Test:

- Navigation.
- Forms.
- State transitions.
- Permission states.
- Emergency UI.
- Location UI.

## End-to-End

Critical flows:

1. Registration.
2. Family creation.
3. Family invitation.
4. Location sharing.
5. Geofence alert.
6. SOS.
7. Chat.
8. Reminder.

---

# 30. Milestones

## Milestone 1 — Project Foundation

Deliverables:

- Repository.
- Monorepo structure.
- TypeScript configuration.
- ESLint.
- Prettier.
- Git hooks if needed.
- Docker Compose.
- MongoDB connection.
- Redis connection.
- Express server.
- React Native project.
- React web project.
- Environment configuration.
- CI pipeline.

Definition of Done:

- All apps run locally.
- Backend health endpoint works.
- MongoDB connects.
- Redis connects.
- CI passes.

---

## Milestone 2 — Authentication

Deliverables:

- Register.
- Login.
- Logout.
- Refresh tokens.
- Email verification architecture.
- Password reset.
- User profile.

Definition of Done:

- Authenticated API requests work.
- Unauthorized requests are rejected.
- Refresh token rotation works.
- Passwords are never stored in plain text.

---

## Milestone 3 — Family Management

Deliverables:

- Create family.
- Join family.
- Invite member.
- Accept invitation.
- Reject invitation.
- Family member list.
- Roles.
- Permissions.

Definition of Done:

- User can create a family.
- Users can join through invitation.
- Authorization is enforced server-side.
- Family members cannot access unrelated families.

---

## Milestone 4 — Mobile Permission Foundation

Deliverables:

- Location permission flow.
- Notification permission flow.
- Permission status screen.
- Device registration.
- Push token registration.

Definition of Done:

- Android and iOS permission states are handled.
- Device push token reaches backend.
- Permission changes are reflected.

---

## Milestone 5 — Location Tracking

Deliverables:

- Foreground location.
- Background location foundation.
- Location API.
- Latest location in Redis.
- Persistent history sampling.
- Location map.
- Last updated status.

Definition of Done:

- Child can share location.
- Authorized parent can see location.
- Unauthorized user cannot.
- Offline/recent/unknown states are represented.

---

## Milestone 6 — Real-Time Location

Deliverables:

- Socket.IO server.
- Family rooms.
- Location events.
- Parent live map updates.
- Presence.

Definition of Done:

```text
Child moves
→ Backend receives
→ Redis updated
→ Socket event emitted
→ Authorized parent map updates
```

---

## Milestone 7 — Places and Geofencing

Deliverables:

- Create place.
- Create geofence.
- Assign members.
- Entry detection.
- Exit detection.
- Event deduplication.
- Geofence notifications.

Definition of Done:

- Parent creates a safe zone.
- Assigned member enters/leaves.
- Correct event is generated.
- Correct users are notified.
- Boundary GPS noise does not spam alerts.

---

## Milestone 8 — Push Notification System

Deliverables:

- FCM integration.
- Device tokens.
- Notification service.
- Notification collection.
- Read/unread state.
- Deep links.

Definition of Done:

- Push notification reaches correct device.
- Notification opens the correct screen.
- Multiple devices are supported.
- Invalid tokens are handled.

---

## Milestone 9 — Emergency / SOS

Deliverables:

- SOS button.
- Emergency creation.
- Guardian notification.
- Emergency state.
- Emergency screen.
- Live emergency location.
- Acknowledge.
- Resolve.
- Emergency history.

Definition of Done:

```text
Child presses SOS
→ Emergency created
→ Authorized guardians notified
→ Emergency screen opens
→ Live location available
→ Guardian acknowledges
→ Emergency resolved
```

---

## Milestone 10 — Family Chat

Deliverables:

- Family chat.
- Socket.IO messages.
- MongoDB persistence.
- Offline message handling.
- Push notification.
- Read status.

Definition of Done:

- Authorized family members can communicate.
- Unauthorized users cannot access messages.
- Messages persist.
- Offline recipients receive notifications.

---

## Milestone 11 — Reminders and Background Jobs

Deliverables:

- Create reminder.
- Assign reminder.
- Scheduled reminder.
- Recurring reminder.
- BullMQ workers.
- Push notification.
- Reminder history.

Definition of Done:

- Scheduled reminders execute reliably.
- Duplicate notifications are prevented.
- Failed jobs can be retried.

---

## Milestone 12 — Safety Check-In

Deliverables:

- Create check-in.
- Assign member.
- Deadline.
- Response.
- Overdue state.
- Parent notification.

---

## Milestone 13 — Tasks and Calendar

Deliverables:

- Family tasks.
- Chores.
- Task assignment.
- Completion.
- Optional points.
- Calendar events.
- Event reminders.

---

## Milestone 14 — Privacy and Security Hardening

Deliverables:

- Permission audit.
- Sensitive endpoint review.
- Rate limiting.
- Audit logs.
- Session management.
- Account deletion.
- Data retention.
- Location privacy settings.
- Security headers.
- Input validation review.

---

## Milestone 15 — Testing

Deliverables:

- Unit tests.
- Integration tests.
- Socket tests.
- Mobile tests.
- Critical E2E tests.
- Load testing for location updates.
- Notification reliability testing.

---

## Milestone 16 — Production Infrastructure

Deliverables:

- Production MongoDB.
- Production Redis.
- Backend deployment.
- Web deployment.
- Mobile build configuration.
- Firebase production configuration.
- Monitoring.
- Logging.
- Error tracking.
- Backups.
- CI/CD.

---

# 31. Development Phases

The milestones above should be executed in this order.

## Phase 1 — Foundation

Milestones:

1

Goal:

Create a stable development environment.

---

## Phase 2 — Identity and Family

Milestones:

2–3

Goal:

Users, authentication, families, roles, permissions.

---

## Phase 3 — Mobile Permissions and Devices

Milestone:

4

Goal:

Prepare mobile devices for location and notification capabilities.

---

## Phase 4 — Location Platform

Milestones:

5–7

Goal:

Build location, real-time updates, places, and geofencing.

---

## Phase 5 — Safety

Milestones:

8–9

Goal:

Build push notifications and SOS/emergency functionality.

---

## Phase 6 — Communication

Milestone:

10

Goal:

Build real-time family communication.

---

## Phase 7 — Organization

Milestones:

11–13

Goal:

Reminders, check-ins, tasks, chores, and calendar.

---

## Phase 8 — Production Hardening

Milestones:

14–16

Goal:

Security, testing, deployment, monitoring, reliability.

---

# 32. Future Phase — Advanced Features

Only begin after the MVP is stable.

## School Module

- School profile.
- School timings.
- Class information.
- School events.
- Pickup location.
- School check-in.

## Transportation

- Bus tracking.
- Pickup/drop-off.
- Driver information.
- ETA.

## Finance

- Expenses.
- Allowance.
- Budgets.
- Spending history.

## Rewards

- Chore points.
- Family goals.
- Rewards.

## Travel

- Trip creation.
- Itinerary.
- Shared location.
- Travel documents.
- Trip expenses.

## Family Vault

- Secure documents.
- Categories.
- Access permissions.
- Expiration reminders.

## AI Assistant

Examples:

```text
"What does my family have planned tomorrow?"
"Which reminders are due today?"
"Who has not completed their check-in?"
"Create a reminder for everyone at 7 PM."
```

The AI must only access information authorized for the requesting user.

---

# 33. Location Data Retention

Define retention before production.

Example policy:

```text
Latest location:
Retain while sharing is active.

Detailed location history:
Configurable retention period.

Emergency location:
Longer retention may be required for incident history.

Deleted account:
Delete or anonymize associated data according to the product's documented policy and applicable requirements.
```

The exact policy should be reviewed for the target markets and legal requirements.

---

# 34. Performance Requirements

The backend should be designed for high-frequency location traffic.

Do not write every GPS event directly to MongoDB.

Preferred architecture:

```text
GPS
 ↓
API / Socket
 ↓
Validation
 ↓
Redis latest state
 ↓
Socket.IO
 ↓
Parents
```

Selected events:

```text
Location
 ↓
Sampling / processing
 ↓
MongoDB history
```

Emergency tracking can temporarily use a higher update frequency.

---

# 35. Reliability Requirements

For critical events:

```text
SOS
Geofence alert
Safety check-in overdue
```

Do not rely on one communication channel.

Use:

```text
Persistent event
+
Push notification
+
Socket.IO when connected
```

Important events should be idempotent.

---

# 36. Offline Behavior

## Child device offline

Display:

```text
Last seen 12 minutes ago
```

Do not display stale data as live.

## Parent offline

When parent reconnects:

- Fetch latest location.
- Fetch unread notifications.
- Fetch active emergencies.
- Reconnect Socket.IO.
- Synchronize relevant state.

## Child loses network

Location events may be queued locally subject to privacy, storage, and battery constraints.

---

# 37. Error Handling

Use consistent API responses.

Example:

```json
{
  "success": false,
  "error": {
    "code": "GEOFENCE_NOT_FOUND",
    "message": "Geofence not found."
  }
}
```

Never expose internal stack traces to clients.

Use centralized error middleware.

---

# 38. API Conventions

Use:

```text
/api/v1
```

Use plural resource names.

Use HTTP semantics consistently:

```text
GET     Read
POST    Create
PATCH   Update
DELETE  Delete
```

Return appropriate status codes.

---

# 39. Coding Standards

Backend:

- TypeScript strict mode.
- Small controllers.
- Service layer for business logic.
- Repository/data-access layer where useful.
- DTO/schema validation.
- No business logic inside route declarations.
- Centralized error handling.

Frontend:

- Feature-based architecture.
- Reusable components.
- API layer separated from UI.
- Server state managed through TanStack Query.
- Local UI state through Zustand or component state.
- Avoid unnecessary global state.

---

# 40. Git Strategy

Recommended branches:

```text
main
develop
feature/*
fix/*
hotfix/*
```

Commit examples:

```text
feat(auth): add refresh token rotation
feat(location): add latest location service
feat(geofence): implement exit detection
fix(notification): prevent duplicate push alerts
refactor(family): extract permission service
test(emergency): add emergency lifecycle tests
```

---

# 41. Definition of MVP

The first public MVP should contain:

### Required

- Authentication.
- User profile.
- Family creation.
- Family invitations.
- Roles.
- Permissions.
- Location sharing.
- Live location.
- Location history.
- Map.
- Geofencing.
- Push notifications.
- SOS.
- Emergency live tracking.
- Family chat.
- Reminders.
- Safety check-ins.
- Privacy controls.

### Can wait

- Expenses.
- Allowance.
- School.
- Transportation.
- AI.
- Family vault.
- Travel.
- Advanced analytics.
- Rewards.

---

# 42. MVP User Journey

## Parent

```text
Register
 ↓
Create Family
 ↓
Invite Child
 ↓
Child accepts
 ↓
Configure permissions
 ↓
Child enables location
 ↓
Parent sees child on map
 ↓
Parent creates School geofence
 ↓
Child leaves school
 ↓
Parent receives notification
```

## Emergency

```text
Child opens app
 ↓
Presses SOS
 ↓
Emergency created
 ↓
Parent receives push
 ↓
Parent opens emergency
 ↓
Live location shown
 ↓
Parent acknowledges
 ↓
Child is safe
 ↓
Emergency resolved
```

---

# 43. Non-Functional Requirements

The application should be:

- Secure.
- Privacy-conscious.
- Scalable.
- Maintainable.
- Testable.
- Observable.
- Fault tolerant.
- Mobile-friendly.
- Responsive.
- Accessible where practical.

Critical safety features should prioritize reliability over cosmetic features.

---

# 44. Important Product Rules

1. A child must never automatically become visible to unrelated users.
2. Family membership must always be verified server-side.
3. Location access must be permission-based.
4. A stale location must never be presented as live.
5. SOS must have a persistent backend record.
6. SOS must use push notification in addition to sockets.
7. Geofence events must be deduplicated.
8. Notifications must not reveal more location information than necessary.
9. Sensitive data must not appear in logs.
10. AI must never receive unrestricted database access.
11. Client-side permissions are never trusted.
12. Emergency functionality must work even when the parent app is backgrounded, subject to platform notification behavior.
13. The application must clearly communicate location-sharing status.
14. The system should avoid unnecessary continuous GPS usage to preserve battery.
15. Location history should have an explicit retention policy.

---

# 45. Recommended Implementation Order Summary

```text
01. Repository + tooling
        ↓
02. Backend foundation
        ↓
03. Database
        ↓
04. Authentication
        ↓
05. User profile
        ↓
06. Family management
        ↓
07. Roles + permissions
        ↓
08. Mobile permissions
        ↓
09. Device registration
        ↓
10. Location sharing
        ↓
11. Redis latest location
        ↓
12. Socket.IO
        ↓
13. Live map
        ↓
14. Location history
        ↓
15. Places
        ↓
16. Geofencing
        ↓
17. Push notifications
        ↓
18. SOS
        ↓
19. Emergency live tracking
        ↓
20. Family chat
        ↓
21. Reminders
        ↓
22. Safety check-ins
        ↓
23. Tasks
        ↓
24. Calendar
        ↓
25. Security hardening
        ↓
26. Testing
        ↓
27. Deployment
        ↓
28. Monitoring
        ↓
29. Advanced modules
```

---

# 46. LLM Development Instructions

When using this specification with an LLM to implement ParentGuide:

## General Rules

- Do not skip dependencies between phases.
- Do not implement future modules before their required foundation exists.
- Do not rewrite working architecture without a concrete reason.
- Preserve existing APIs unless a migration is explicitly planned.
- Use TypeScript.
- Follow the repository structure.
- Follow the permission model.
- Validate all external input.
- Add tests for important business logic.
- Do not hard-code secrets.
- Do not put authorization only on the client.
- Do not treat Socket.IO as the only delivery mechanism for critical notifications.
- Do not treat client location data as trusted.
- Do not store high-frequency transient location data unnecessarily in MongoDB.

## Before Implementing a Feature

The LLM should determine:

1. Which module owns the feature?
2. Which database models are involved?
3. Which permissions are required?
4. Which API endpoints are required?
5. Whether Socket.IO is required.
6. Whether Redis is required.
7. Whether a background job is required.
8. Whether push notification is required.
9. Which mobile permissions are required.
10. Which tests are required.

## Output Expected From an LLM

For each implementation task, provide:

```text
1. What is being implemented.
2. Files to create/change.
3. Database changes.
4. API changes.
5. Socket events if applicable.
6. Frontend/mobile changes.
7. Security considerations.
8. Tests.
9. How to run/verify.
```

Do not modify unrelated modules.

---

# 47. First Development Sprint

The first sprint should contain only:

```text
TASK 1
Initialize monorepo.

TASK 2
Create API application.

TASK 3
Create mobile application.

TASK 4
Create web application.

TASK 5
Configure TypeScript.

TASK 6
Configure ESLint + Prettier.

TASK 7
Configure Docker Compose.

TASK 8
Connect MongoDB.

TASK 9
Connect Redis.

TASK 10
Create environment configuration.

TASK 11
Create health endpoint.

TASK 12
Create basic CI workflow.

TASK 13
Create initial documentation.

TASK 14
Create User model.

TASK 15
Create authentication module.
```

Do not begin location tracking during Sprint 1.

---

# 48. First Production Target

The first production-capable version should demonstrate:

```text
Authentication
+
Family
+
Roles
+
Location
+
Map
+
Geofence
+
Push Notification
+
SOS
+
Chat
+
Reminders
```

This is the core ParentGuide experience.

---

# 49. Final Product Vision

ParentGuide should eventually become a unified family platform:

```text
                    PARENTGUIDE
                         |
       +-----------------+-----------------+
       |                 |                 |
     FAMILY            SAFETY           LOCATION
       |                 |                 |
   Members             SOS             Live Map
   Roles               Alerts          History
   Permissions         Check-ins       Geofences
   Profiles            Contacts        Places
       |
       +-----------------+-----------------+
                         |
                 COMMUNICATION
                         |
                  Chat / Announcements
                         |
       +-----------------+-----------------+
       |                 |                 |
   ORGANIZATION       ACTIVITIES        SMART
       |                 |                 |
   Reminders           Tasks            AI
   Calendar            Chores           Insights
   Shopping            Rewards          Assistance
       |
       +-----------------+-----------------+
                         |
                     EXTENSIONS
                         |
               School / Travel / Finance
               Transportation / Documents
```

The product should be developed incrementally. The foundation must remain simple and reliable, while advanced modules are added only after authentication, authorization, location, notification, real-time communication, and emergency systems are stable.

**End of ParentGuide Project Specification**
