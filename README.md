# CivicLens — AI-Powered Public Intelligence Platform

A full-stack platform that lets users query real NYC public datasets using plain English, visualize results on an interactive map, and receive real-time alerts.

**Demo query:** "Show me noise complaints in Brooklyn last 30 days near parks" → Claude parses it → Elasticsearch fires → results pin to Mapbox → Celery watches for new matches → WebSocket alert.

## Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.11 + Django 4.2 + Django REST Framework |
| Database | PostgreSQL 15 + PostGIS (geospatial) |
| Search | Elasticsearch 8 + django-elasticsearch-dsl |
| Task Queue | Celery 5 + Redis 7 + django-celery-beat |
| WebSocket | Django Channels 4 + channels-redis |
| AI | Claude claude-sonnet-4-6 (tool calling + agentic mode) |
| Frontend | React 18 + Redux Toolkit + Mapbox GL JS + Vite |
| Infra | Docker Compose (dev) · GitHub Actions CI |

## Data Sources (free, no auth required)

- **NYC 311** — 30M+ service requests via Socrata API (`data.cityofnewyork.us`)
- **NYPD Crime Stats** — complaint data via NYC Open Data
- **MTA Subway Alerts** — real-time transit disruptions via MTA RSS feed
- **FEMA** — disaster declarations (optional, add to `ingestion/sources/`)

## Quick Start

```bash
cp .env.example .env
# Fill in ANTHROPIC_API_KEY and VITE_MAPBOX_TOKEN

docker compose up --build

# In a second terminal, run migrations + seed ES index
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py search_index --rebuild

# Trigger first ingestion manually
docker compose exec backend python manage.py shell -c "from apps.ingestion.tasks import run_all_ingestion; run_all_ingestion()"
```

Frontend: http://localhost:5173  
Backend API: http://localhost:8000  
Django Admin: http://localhost:8000/admin

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/incidents/` | Paginated incident list |
| GET | `/api/search/?q=noise&borough=Brooklyn&days=30` | Elasticsearch full-text + geo search |
| POST | `/api/ai/chat/` | Natural language → tool calls → answer |
| POST | `/api/ai/agent/` | Autonomous multi-step agent |
| GET | `/api/alerts/` | Active alert subscriptions |
| WS | `ws://localhost:8000/ws/alerts/` | Live incident push feed |

## AI Tool-Calling Flow

```
User: "noise complaints in Brooklyn last 30 days near parks"
  ↓
Claude claude-sonnet-4-6 → tool_use: search_incidents({query: "noise", borough: "Brooklyn", days: 30})
  ↓
Backend executes Elasticsearch query → returns 847 results
  ↓
Claude → tool_use: aggregate_stats({group_by: "neighborhood", borough: "Brooklyn", days: 30})
  ↓
Backend queries Postgres → returns top neighborhoods by count
  ↓
Claude → end_turn: "Brooklyn had 847 noise complaints in the last 30 days. Bushwick (234) and Bed-Stuy (198) lead..."
  ↓
Frontend renders text + pins 847 locations on Mapbox map
```

## Architecture Decision Record

### ADR-001: Celery + Redis in dev vs Kafka in production

**Status:** Accepted  
**Date:** 2024-01

**Context:**  
The ingestion pipeline needs a message queue for async data ingestion tasks and the alert system needs a pub/sub mechanism to fan out new incidents to WebSocket clients.

**Decision:**  
Use Celery + Redis in development instead of Kafka.

**Reasoning:**  
Kafka (with KRaft or ZooKeeper) adds 2-3 containers, requires broker configuration, and has meaningful operational overhead with no dev benefit when message throughput is low (< 1000 msg/day in dev). Celery provides the same logical abstraction — producers schedule tasks, consumers process them — without the setup cost.

**Production migration path:**  
The codebase is structured so that only the transport layer needs to swap:

1. `apps/ingestion/tasks.py` — Replace `@shared_task` decorators with `confluent-kafka` producers publishing to a `raw-incidents` topic
2. `apps/alerts/tasks.py` — Replace Celery beat with a Kafka consumer group subscribing to `processed-incidents`  
3. `config/settings/base.py` — Add `KAFKA_BOOTSTRAP_SERVERS` setting; keep `CHANNEL_LAYERS` (Redis stays for WebSocket fan-out)

**Zero model/API changes required** — all Django models, serializers, Elasticsearch documents, and REST endpoints remain identical.

**Consequences:**  
- Dev: single `redis` container, simple setup
- Prod: Kafka handles terabyte-scale throughput with replay, consumer group parallelism, and durable logs
- The ADR itself demonstrates systems-thinking: knowing *when* to add complexity, not just *how* to
