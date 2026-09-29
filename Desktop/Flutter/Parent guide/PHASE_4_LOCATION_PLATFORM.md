# Phase 4 — Location Platform

## Milestones:
5–7

## Goal:
Build location, real-time updates, places, and geofencing.

## Milestone 5 — Location Tracking Details:
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

## Milestone 6 — Real-Time Location Details:
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

## Milestone 7 — Places and Geofencing Details:
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