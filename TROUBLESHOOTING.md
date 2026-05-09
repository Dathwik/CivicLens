# CivicLens — Setup Debugging Log

A record of every issue hit during the first end-to-end bring-up, in the order we hit them. Useful as reference for re-bootstrapping the project from scratch or onboarding someone else.

---

## 1. `ModuleNotFoundError: No module named 'debug_toolbar'`

**Symptom:** `backend`, `celery-worker`, and `celery-beat` containers all crashed on boot with the same import error during `apps.populate(settings.INSTALLED_APPS)`.

**Root cause:** [backend/Dockerfile](backend/Dockerfile) installed only `requirements/base.txt`, but `DJANGO_SETTINGS_MODULE` was hard-wired to `config.settings.local`, which imports `debug_toolbar` (declared only in `requirements/local.txt`).

**Fix:** Changed the Dockerfile to install `local.txt`:
```dockerfile
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/local.txt
```

**Why:** `local.txt` does `-r base.txt` then adds dev tools (pytest, ipython, factory-boy, debug-toolbar). Since the only settings module the image points at is `local.py`, the image must always have those deps. The split would only make sense once a `production.py` settings module exists.

---

## 2. `ModuleNotFoundError: No module named 'django_filters'`

**Symptom:** Same crash pattern, next dep down.

**Root cause:** `apps/incidents/views.py` imports `from django_filters.rest_framework import DjangoFilterBackend`, but `django-filter` was never pinned in any requirements file.

**Fix:** Added `django-filter==23.5` to `requirements/base.txt` and registered `"django_filters"` in `THIRD_PARTY_APPS` in [config/settings/base.py](backend/config/settings/base.py).

**Why:** Code-vs-deps drift — the model imports were never reflected back into `requirements`. After this, I ran a one-shot grep across the whole backend (`grep -rhE "^(import|from)" --include="*.py"`) to confirm every other third-party import was already covered, so we wouldn't loop on this.

---

## 3. `ModuleNotFoundError: No module named 'rest_framework_gis'`

**Symptom:** Same again.

**Root cause:** `apps/incidents/serializers.py` imports `GeoFeatureModelSerializer` from `rest_framework_gis`. Same drift as above.

**Fix:** Added `djangorestframework-gis==1.0` to `requirements/base.txt`.

---

## 4. No migration files exist for local apps

**Symptom:** After `migrate` succeeded, `search_index --rebuild` failed with `psycopg2.errors.UndefinedTable: relation "incidents_incident" does not exist`.

**Root cause:** The repo was committed without ever running `makemigrations`, so `apps/incidents/migrations/` and `apps/alerts/migrations/` directories didn't exist. `migrate` had nothing to apply for those apps.

**Fix:**
```bash
docker compose exec backend python manage.py makemigrations incidents alerts
docker compose exec backend python manage.py migrate
```

**Why:** Migration files are source artifacts and must be checked into git. They're now in [apps/incidents/migrations/0001_initial.py](backend/apps/incidents/migrations/0001_initial.py) and [apps/alerts/migrations/0001_initial.py](backend/apps/alerts/migrations/0001_initial.py).

---

## 5. `celery-beat` crashes on first boot

**Symptom:** After the import errors were fixed, `celery-beat` exited with a `django_celery_beat`-internal traceback when reading its schedule tables.

**Root cause:** Beat starts before migrations run. `docker-compose`'s `depends_on` only waits for the dependency container to *start*, not for `migrate` to *complete*.

**Fix:** Run `migrate` first, then `docker compose restart celery-beat`. Acceptable for dev. The clean fix would be either an init container that runs `migrate` before beat starts, or making beat retry on schema errors.

---

## 6. Celery tries to connect to RabbitMQ instead of Redis

**Symptom:**
```
ConnectionRefusedError: [Errno 111] Connection refused
File ".../kombu/transport/pyamqp.py", line 203, in establish_connection
```
Trying to talk `amqp://` on port 5672 even though `CELERY_BROKER_URL` was `redis://redis:6379/0`.

**Root cause:** [config/__init__.py](backend/config/__init__.py) was empty. The Celery `app` object defined in `config/celery.py` was never registered, so `@shared_task` resolved to the *implicit* default Celery app (whose default broker is `amqp://guest@localhost:5672`).

**Fix:** Added to [config/__init__.py](backend/config/__init__.py):
```python
from .celery import app as celery_app
__all__ = ("celery_app",)
```

**Why:** Standard Django+Celery wiring. Without this import, Celery sees no app, falls back to defaults. Easy to miss because the `celery -A config worker` command works fine (it loads `config/celery.py` directly) — it's only `.delay()` calls from inside Django that break.

---

## 7. Frontend renders pure black, no UI at all

**Symptom:** `localhost:5173` loaded but showed only the dark `#0f1117` body background. No StatsBar, no map, no chat panel.

**Root cause:** The frontend container in [docker-compose.yml](docker-compose.yml) didn't have `env_file: .env`, so `VITE_MAPBOX_TOKEN` was never passed in. `mapboxgl.accessToken` became `""`, the `new mapboxgl.Map(...)` constructor threw inside the `useEffect`, and React's dev-mode error handling unmounted the tree.

**Fix:** Added `env_file: .env` to the frontend service block, then `docker compose up -d --force-recreate frontend`.

**Why:** Vite reads `VITE_*` vars at dev-server start time from the process env. The other env vars in the compose block (`VITE_API_URL`, `VITE_WS_URL`) only worked because they were inlined there, not because Vite read `.env`.

---

## 8. WebSocket connection fails

**Symptom:** Console: `WebSocket connection to 'ws://localhost:8000/ws/alerts/' failed`. The "Live Alerts" status dot stayed red.

**Root cause:** Backend was running `python manage.py runserver`, which is WSGI-only and can't speak WebSockets. Channels 4.x removed the auto-override of `runserver` that earlier versions had.

**Fix:** Changed the backend command in [docker-compose.yml](docker-compose.yml):
```yaml
command: daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

**Trade-off:** Daphne has no autoreloader, so Python edits now require `docker compose restart backend`. Acceptable for dev; a real fix would be `uvicorn --reload` or installing the `daphne` app in `INSTALLED_APPS` *before* `django.contrib.staticfiles` to re-enable the runserver override.

---

## 9. `/api/ai/chat/` returns 500

**Symptom:**
```
anthropic.BadRequestError: Error code: 400 - 'Your credit balance is too
low to access the Anthropic API. Please go to Plans & Billing.'
```

**Root cause:** Not a code bug — Anthropic account had $0.00 in API credits. The key was valid (auth passed), the model name was accepted, the request was well-formed.

**Fix:** Top up at https://console.anthropic.com/settings/billing. No restart needed.

**Note:** The current `ChatView` lets the Anthropic exception bubble up as a generic 500. Future polish: catch `anthropic.APIStatusError` in [apps/ai/views.py](backend/apps/ai/views.py) and surface the message in the JSON response.

---

## 10. `AppRegistryNotReady: Apps aren't loaded yet` from `python -c`

**Symptom:** Running `docker compose exec backend python -c "from apps.incidents.models import Incident; print(Incident.objects.count())"` crashed before the import.

**Root cause:** `python -c` runs raw Python — it doesn't initialize Django. Importing a model touches the app registry, which isn't populated yet.

**Fix:** Use `manage.py shell -c` instead, which calls `django.setup()` first:
```bash
docker compose exec backend python manage.py shell -c "from apps.incidents.models import Incident; print(Incident.objects.count())"
```

---

## 11. Ingestion succeeded but ES index stayed empty

**Symptom:** `Incident.objects.count()` returned 797 but `/api/search/` returned `total: 0`.

**Root cause:** All three ingestion sources used `Incident.objects.bulk_create(ignore_conflicts=True, ...)`. `bulk_create` **skips Django signals**, so `django-elasticsearch-dsl`'s `RealTimeSignalProcessor` never fired and the ES `incidents` index stayed empty.

**Fix:** Added an explicit re-index after every `bulk_create` in each source ([nyc_311.py](backend/apps/ingestion/sources/nyc_311.py), [nyc_crime.py](backend/apps/ingestion/sources/nyc_crime.py), [mta_alerts.py](backend/apps/ingestion/sources/mta_alerts.py)):
```python
qs = Incident.objects.filter(external_id__in=[i.external_id for i in incidents])
IncidentDocument().update(qs)
```
Plus a one-time `search_index --rebuild` to backfill the rows that had been ingested before the patch.

**Why:** `bulk_create` bypasses signals by design (it's a single SQL `INSERT`, no per-row Python). Filtering by `external_id` (the dedup key) re-indexes both newly-inserted rows and any that were skipped due to `ignore_conflicts` — slight overhead, but idempotent and correct.

---

## 12. Borough/category filters return 0 results

**Symptom:** `curl '/api/search/?borough=Brooklyn'` returned `total: 0` even though hundreds of Brooklyn incidents existed in the index. Same for any case (`brooklyn`, `BROOKLYN`).

**Root cause:** `django-elasticsearch-dsl` auto-mapped `borough`, `category`, `source`, `status` as analyzed **Text** fields. ES's standard analyzer lowercases tokens at index time. But `apps/search/utils.py::build_incident_query` filters with `Q("term", borough=borough.title())` — and `term` queries don't apply analyzers, so they look for the literal value in the inverted index. "Brooklyn" never matches the indexed term "brooklyn".

**Fix:** Explicitly declared the filter fields as `KeywordField` in [apps/search/documents.py](backend/apps/search/documents.py):
```python
category = fields.KeywordField()
source = fields.KeywordField()
status = fields.KeywordField()
borough = fields.KeywordField()
```
And removed those names from `Django.fields = [...]` so the explicit declarations win. Then `search_index --rebuild` to apply the new mapping.

**Why:** ES mappings are immutable per index — you can't change a field's type in place, you have to drop and recreate. `title`, `description`, `address` stay as Text fields because they're used with `multi_match` for full-text search.

---

## 13. Top filter-chip row clipped above the viewport

**Symptom:** The category row (`Noise / Crime / Transit / …`) was invisible. Only the borough row showed up at the top of the page, and even its top edge looked cut.

**Root cause:** [StatsBar.jsx](frontend/src/components/Dashboard/StatsBar.jsx) used `flexWrap: "wrap"`. On narrow widths the chips wrapped onto two rows. Combined with `body { overflow: hidden }` in [index.html](frontend/index.html), the second row pushed the first one above the viewport with no way to scroll back to it.

**Fix:** Switched the bar to a single non-wrapping row that scrolls horizontally if it overflows:
```jsx
display: "flex", flexWrap: "nowrap", overflowX: "auto", whiteSpace: "nowrap"
```
Also set `flexShrink: 0` on the wrapper and on each chip group so they keep their natural size instead of being squeezed.

**Why:** Wrapping is fine when the page can scroll vertically, but `overflow: hidden` on `body` made wraps unreachable. One-row + horizontal scroll guarantees nothing gets pushed out of sight.

---

## 14. Map renders empty until you click a chip

**Symptom:** Fresh page load showed a blank dark map. Pins only appeared after clicking a category or borough chip.

**Root cause:** `incidentsSlice` initial state has `geojson: null`. Nothing in [App.jsx](frontend/src/App.jsx) dispatched `searchIncidents` on mount, so the map never had data to render.

**Fix:** Dispatch a default search on mount:
```jsx
useEffect(() => {
  connectAlerts();
  dispatch(searchIncidents({ days: 30 }));
}, [dispatch]);
```

---

## 15. Selecting "Bronx" returns 0 incidents

**Symptom:** DB had 324 Bronx records, but clicking the Bronx chip returned an empty result set.

**Root cause:** Borough name mismatch.
- Ingestion stores `r.get("boro_nm", "").title()` → `"Bronx"` (no article).
- The frontend's `BOROUGHS` array used `"The Bronx"`.
- The ES filter is a `term` query, which is exact-match — `"The Bronx"` ≠ `"Bronx"`.

**Fix:** Renamed the chip in [StatsBar.jsx](frontend/src/components/Dashboard/StatsBar.jsx):
```js
const BOROUGHS = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"];
```

**Why:** The DB is the source of truth — there are six normalized borough strings (`Bronx`, `Brooklyn`, `Manhattan`, `Queens`, `Staten Island`, `Unspecified`). The UI must use those literal values. Same trap as #12: `term` queries don't tolerate any mismatch.

---

## 16. Pins disappear when you zoom the map out

**Symptom:** Zooming out past street level made all the colored circle markers vanish. Heatmap mode still worked, but in pin mode the map went empty.

**Root cause:** [IncidentMap.jsx](frontend/src/components/Map/IncidentMap.jsx) declared the pins layer with `minzoom: 8`. Mapbox skips drawing the layer entirely below that zoom level.

**Fix:** Removed `minzoom` and added a smaller radius stop at zoom 4 so pins scale down gracefully instead of disappearing:
```js
"circle-radius": ["interpolate", ["linear"], ["zoom"], 4, 2, 8, 4, 15, 8],
```

**Why:** The original `minzoom: 8` was probably a perf guard for crowded city-wide views, but the heatmap layer already covers that case better. Letting pins render at all zooms is the expected behavior; perf is fine for the current dataset size (~800 features).

---

## 17. Send button missing from chat panel

**Symptom:** Typing in the chat input worked, but no Send button was visible to the right of the field — even pressing Enter felt like the only way to submit. The suggestion chips ("Show me noise complai…") were also clipped horizontally.

**Root cause:** [App.jsx](frontend/src/App.jsx) defined the layout grid as `gridTemplateColumns: "1fr 180px 180px"` — 180px is far too narrow to hold a flex-1 input plus a Send button side by side, so the button overflowed the column edge and got clipped by the right-hand AlertFeed pane.

**Fix:** Widened the chat column (and the alerts column, which had the same problem with its content):
```jsx
gridTemplateColumns: "1fr 360px 240px"
```

**Why:** The original sizing must have been picked when the panels were narrower / had less content. The clipped suggestion chip was the giveaway — the column couldn't even fit its own static text. Fixed-pixel grid columns are fragile to content growth; if this happens again, switch to `minmax(360px, 1fr)` or similar.

---

## 18. Last 7 / 14 / 30 days filters all show the same incident count

**Symptom:** Selecting different time windows in the StatsBar dropdown returned identical totals (e.g. 497 for all of 7d, 14d, 30d). Only the 90d option produced a different number.

**Root cause:** [nyc_311.py](backend/apps/ingestion/sources/nyc_311.py) and [nyc_crime.py](backend/apps/ingestion/sources/nyc_crime.py) both fetched only the most recent N records (`limit=500` / `limit=300`, `order=created_date DESC`). NYC 311 receives ~25k complaints/day, so 500 records all fell within a ~1-day window. Every 7/14/30/90 day filter matched the same set. Crime, being lower volume, was the only source that actually reached back weeks — which is why 90d differed.

**Fix:** Replaced the "top-N" pull with **weekly time-bucketed pulls** in both sources. Each ingestion loops over `WEEKS_BACK=12` weeks, fetching `PER_WEEK_LIMIT` records per week using a Socrata `$where` clause on `created_date` / `cmplnt_fr_dt`:
```python
for _ in range(weeks_back):
    start = end - timedelta(days=7)
    where = (
        f"created_date >= '{start.strftime('%Y-%m-%dT%H:%M:%S')}' "
        f"AND created_date < '{end.strftime('%Y-%m-%dT%H:%M:%S')}'"
    )
    batch = client.get(DATASET_ID, where=where, limit=per_week_limit, order="created_date DESC", select=...)
    records.extend(batch)
    end = start
```

After re-running ingestion: 7d=892, 14d=1,285, 30d=2,078, 90d=6,625.

**Why:** Socrata's `between … and …` SoQL form 500'd here (one query was the trace id, no useful error body). The `>= AND <` two-clause form works reliably and produces non-overlapping buckets. MTA alerts are real-time and don't need bucketing.

---

## 19. Map shows fewer pins than the StatsBar count claims

**Symptom:** StatsBar reported "6,625 incidents" but the Mapbox layer rendered ~50 dots clustered in Manhattan. Same shape for any filter — the count was always the true total, the map was always a tiny subset.

**Root cause:** [apps/search/views.py](backend/apps/search/views.py) built the response's `geojson` from the same paginated `hits` list it used for `results`. With `page_size=50` (default), the geojson always had ≤50 features regardless of how many incidents matched.

**Fix:** Split the endpoint's two outputs. `results` stays paginated; `geojson` runs a separate ES query with `size=10000` (`GEO_CAP`, the index `max_result_window` default) and only the fields needed for plotting:
```python
geo_search = (
    IncidentDocument.search()
    .query(query)
    .source(["title", "category", "borough", "timestamp", "location"])
    .extra(size=GEO_CAP)
)
```

After the fix and a `docker compose restart backend` (Daphne doesn't autoreload — see #8), the API returns geojson feature counts equal to `total` for every window we tested.

**Why:** The two outputs serve different consumers. A future incident-list view needs pagination. The map needs every matching point to plot the heatmap and individual markers correctly. Sharing one paginated query was a hidden coupling that quietly broke the map as soon as the dataset grew past 50.

---

## Things that looked like problems but weren't

- **`postgres` platform mismatch warning** (`linux/amd64 vs linux/arm64/v8` on Apple Silicon) — runs fine under emulation, just slower. No action needed for dev.
- **`events.mapbox.com ERR_BLOCKED_BY_CLIENT`** — ad-blocker eating Mapbox telemetry. Map still works.
- **`favicon.ico 404`** — cosmetic, no favicon configured.
- **`docker-compose.yml: the attribute version is obsolete`** — Compose v2 ignores `version: "3.9"`. Safe to delete the line.
- **Naive datetime warnings during ingestion** (`DateTimeField received a naive datetime ... while time zone support is active`) — NYC 311's `created_date` lacks tz info; Django stores it but logs the warning. Could be silenced by parsing into `timezone.make_aware(...)` in the ingestion source.
- **NYPD crime data heavily Bronx-skewed** — looks like a borough filter bias but isn't. Socrata's NYPD dataset publishes in batches and the most-recent batches we sample happen to be Bronx-heavy. Issue #18 widened the time window to 12 weeks of weekly buckets, which spread the data across boroughs better but didn't fully fix the skew. Looping per borough with `where=boro_nm='X'` would balance it out if you need parity.

---

## The bring-up sequence (clean run)

After all fixes:

```bash
cp .env.example .env                 # then fill ANTHROPIC_API_KEY + VITE_MAPBOX_TOKEN
docker compose up --build            # foreground; wait for ES "started" + backend "Listening on TCP"

# in a second terminal:
docker compose exec backend python manage.py makemigrations incidents alerts
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py search_index --rebuild     # type "y"
docker compose restart celery-beat   # so it picks up its newly-existent tables
docker compose exec backend python manage.py shell -c \
    "from apps.ingestion.tasks import run_all_ingestion; run_all_ingestion()"
```

Then http://localhost:5173 — click any borough/category chip to populate the map.
