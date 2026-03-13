# Dailymotion Moderation Technical Test

## Overview

This project implements the two services required by the technical test:

- **Moderation API**: manages the moderation queue lifecycle
- **Dailymotion API Proxy**: returns video information through a proxy layer with Redis caching

The project is fully containerized and can be started and tested with **Docker** and **Docker Compose** only.

## Architecture

The architecture choices and system diagram are documented in:

```text
infra/diagrams/architecture.md
```

This document includes:

- the architecture overview
- the technical choices
- a Mermaid diagram of the system

## Services

### Moderation API

The Moderation API exposes the moderation workflow endpoints:

```text
POST /add_video
```

```text
GET /get_video
```

```text
POST /flag_video
```

```text
GET /stats
```

```text
GET /log_video/{video_id}
```

Implemented behaviors:

- videos are inserted in the queue with status pending
- the moderation queue follows FIFO
- the same moderator always gets the same in_review video until it is flagged
- different moderators get different videos
- moderation decisions are persisted in PostgreSQL
- audit logs are recorded for each relevant state transition

## Proxy

The Proxy API exposes:

```text
GET /get_video_info/{video_id}
```

Implemented behaviors:

- if video_id ends with **404**, the API returns **404 Not Found**
- otherwise, the API returns a coherent mocked video payload
- responses are cached in Redis
- cache hits and cache misses are transparent to the client

## Tech stack

- Python 3.11
- FastAPI
- PostgreSQL
- Redis
- SQLAlchemy Core
- pytest
- Docker / Docker Compose

## Project structure

```
.
├── infra/
│   ├── diagrams/
│   │   └── architecture.md
│   └── postgres/
│       └── init.sql
├── services/
│   ├── moderation_api/
│   └── proxy_api/
├── .env.example
├── docker-compose.yml
└── README.md
```

## Prerequisites

You only need:

- Docker
- Docker Compose

No local Python, PostgreSQL, or Redis installation is required to run the project or the tests.

## Configuration

Create your local environment file from the example:

```bash
cp .env.example .env
```

If you are on Windows **cmd**:

```cmd
copy .env.example .env
```

The project relies on environment variables for:

- PostgreSQL connection
- Redis connection
- API ports
- cache TTL
- log level

## Run the project

Start the full stack:

```bash
docker compose up --build
```

Run it in detached mode:

```bash
docker compose up -d --build
```

Check container status:

```bash
docker compose ps
```

## Health checks

### Moderation API

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{ "status": "ok" }
```

### Proxy API

```bash
curl http://localhost:8001/health
```

Expected response:

```json
{ "status": "ok" }
```

## Run the tests

### Moderation API tests

```bash
docker compose run --rm moderation_api pytest -q
```

### Proxy API tests

```bash
docker compose run --rm proxy_api pytest -q
```

### Run all tests

```bash
docker compose run --rm moderation_api pytest -q
docker compose run --rm proxy_api pytest -q
```

## Reset the environment

```bash
docker compose down -v --remove-orphans
docker compose up -d --build
```

## API summary

### Ports

- Moderation API: http://localhost:8000
- Proxy API: http://localhost:8001
- PostgreSQL (host access): localhost:5433
- Redis (host access): localhost:6379

**POST /add_video**
Adds a video to the moderation queue.

Request

```json
{
  "video_id": "123456"
}
```

Success response

```http
201 Created
```

```json
{
  "video_id": "123456",
  "status": "pending",
  "assigned_to": null
}
```

**GET /get_video**
Returns the current video for a moderator, or assigns the next pending one.

Required header

```http
Authorization: <base64-encoded moderator name>
```

Example for **john.doe**:

```text
am9obi5kb2U=
```

```json
Success response
200 OK
{
  "video_id": "123456",
  "status": "in_review",
  "assigned_to": "john.doe"
}
```

**POST /flag_video**
Flags an in_review video as spam or not spam.

Required header

```http
Authorization: <base64-encoded moderator name>
```

```json
Request
{
  "video_id": "123456",
  "status": "not spam"
}
```

Success response

```http
200 OK
```

```json
{
  "video_id": "123456",
  "status": "not spam"
}
```

**GET /stats**
Returns moderation counters.

```http
Success response
200 OK
```

```json
{
  "total_pending_videos": 0,
  "total_spam_videos": 0,
  "total_not_spam_videos": 0
}
```

**GET /log_video/{video_id}**
Returns the audit history of a video.

```http
Success response
200 OK
```

```json
[
  {
    "date": "2026-01-01T12:00:00+00:00",
    "status": "pending",
    "moderator": null
  },
  {
    "date": "2026-01-01T13:00:00+00:00",
    "status": "in_review",
    "moderator": "john.doe"
  },
  {
    "date": "2026-01-01T14:00:00+00:00",
    "status": "spam",
    "moderator": "john.doe"
  }
]
```

**GET /get_video_info/{video_id}**
Returns video information through the proxy API.

```html
Success response 200 OK
```

```json
{
  "title": "Dailymotion Spirit Movie",
  "channel": "creation",
  "owner": "Dailymotion",
  "filmstrip_60_url": "https://www.dailymotion.com/thumbnail/video/123456",
  "embed_url": "https://www.dailymotion.com/embed/video/123456"
}
```

Not found rule
If **video_id ends** with **404**, the service returns:

```http
404 Not Found
```

```json
{
  "detail": "Video not found",
  "error_code": "video_not_found"
}
```

## Notes and design choices

- PostgreSQL is used as the source of truth for the moderation domain.
  -Redis is used only as a cache for the proxy API.
  -SQLAlchemy Core is used instead of an ORM, in line with the technical constraints.
  -Audit logging is implemented through the **video_logs** table. -**not spam** is exposed at API level, while not_spam is stored internally in the database.
  -The moderation queue logic is implemented with SQL-level safeguards for FIFO and atomic assignment.
  -The Proxy API uses a mocked upstream payload, as allowed by the test statement.

## Manual validation examples

### Get moderation stats

```bash
curl http://localhost:8000/stats
```

### Add a video

```bash
curl -X POST http://localhost:8000/add_video \
  -H "Content-Type: application/json" \
  -d '{"video_id":"123456"}'
```

### Get a video for a moderator

```bash
curl http://localhost:8000/get_video \
  -H "Authorization: am9obi5kb2U="
```

### Flag a video

```bash
curl -X POST http://localhost:8000/flag_video \
  -H "Authorization: am9obi5kb2U=" \
  -H "Content-Type: application/json" \
  -d '{"video_id":"123456","status":"spam"}'
```

### Query the proxy API

```bash
curl http://localhost:8001/get_video_info/123456
```

## Final note

This repository is intentionally structured with:

- a thin HTTP layer
- a service layer for business orchestration
- a repository/cache layer for persistence and infrastructure concerns

This keeps the code testable, explicit, and aligned with the technical requirements.
