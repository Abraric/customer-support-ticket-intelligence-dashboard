# Customer Support Ticket Intelligence & Product Telemetry Dashboard — Output Walkthrough

This guide explains how data flows through the system, what artifacts get produced, and how to validate the results end-to-end.

---

## 1. Data Generation & Staging

| Component | Script | Output |
|-----------|--------|--------|
| Synthetic Support Tickets | `python etl/ticket_etl.py --generate-raw --records 1800` | `data/raw_tickets.csv` (1.8k tickets) |
| Synthetic Telemetry | `python etl/telemetry_etl.py --generate-raw --records 8000` | `data/raw_telemetry.csv` (8k events) |

Both scripts create Cohesity-themed issues (backup failures, ransomware alerts, node offline, etc.) and store them under `data/`. The raw files double as seed data for demos or further experimentation.

---

## 2. NLP-Enriched ETL Output

Running the ETL modules **without** `--generate-raw` consumes existing CSVs, cleans them, and adds features:

- Ticket ETL (`etl/ticket_etl.py`)
  - Resolution hours
  - Severity score (1–4)
  - Predicted category (spaCy rules)
  - HuggingFace sentiment label + score
  - Output: `data/processed/tickets_processed.csv`

- Telemetry ETL (`etl/telemetry_etl.py`)
  - Health severity (Critical/High/Elevated/Normal)
  - Product assignment per node
  - Response-time buckets
  - Output: `data/processed/telemetry_processed.csv`

Each run logs progress via `loguru` and overwrites the processed files to keep the pipeline deterministic.

---

## 3. Database Initialization

```bash
python database/init_db.py
```

- Creates tables defined in `database/schema.sql` via SQLAlchemy models.
- Loads the processed CSVs into:
  - `tickets`
  - `ticket_nlp`
  - `telemetry`
  - `ticket_summary` (aggregated via `refresh_summary()`)
- Default database: `data/support_analytics.db` (SQLite). Switch to PostgreSQL by changing `DATABASE_URL` in `.env`.

**Validation Tip:** open the SQLite file with DB Browser or run:

```sql
SELECT category, ticket_count, avg_resolution_hours
FROM ticket_summary
ORDER BY ticket_count DESC;
```

---

## 4. FastAPI Service Output

Start the API:

```bash
uvicorn api.main:app --reload --port 8000
```

Swagger docs: `http://localhost:8000/docs`

### Key Endpoints

| Endpoint | Description | Sample Output |
|----------|-------------|----------------|
| `GET /api/tickets/top-categories` | Category ranking with counts and avg resolution time | `[{"category":"Backup Failure","ticket_count":412,"avg_resolution_hours":18.4}, ...]` |
| `GET /api/tickets/sentiment-summary` | Sentiment distribution (%) across all tickets | `{"positive_percent":14.3,"negative_percent":63.2,"neutral_percent":22.5}` |
| `GET /api/tickets/trends` | 30-day ticket volume trend | `[{"date":"2024-08-20","ticket_count":54}, ...]` |
| `GET /api/telemetry/events?product=Cohesity%20DataProtect&severity=High&timeframe=7` | Filtered telemetry feed for dashboards | Latest rows with node health context |

These endpoints are designed for Power BI “Web” connectors and for quick JSON validation with `httpie`/`curl`.

---

## 5. Power BI Dashboard Outputs

1. Connect Power BI Desktop to `data/support_analytics.db` (SQLite connector) **and** the FastAPI endpoints (Web connector). Detailed instructions + DAX examples live in `powerbi/instructions.md`.
2. Recommended visuals:
   - Ticket Volume Trend line chart
   - Category Breakdown pie
   - Sentiment KPI cards
   - Issue Heatmap (product × severity)
   - Telemetry Spike detector (area chart)
   - AI Summary card (top risk indicators)
3. Export screenshots to `powerbi/images/` (placeholders listed in the instructions file) for portfolio showcases.

---

## 6. Dockerized Output

```bash
cd docker
docker compose up --build
```

The compose command:
1. Builds the Python 3.11 image.
2. Runs both ETL scripts.
3. Executes `database/init_db.py`.
4. Launches FastAPI on `localhost:8000`.

This produces the same processed CSVs and SQLite DB inside the mounted `data/` volume, ensuring reproducible results for demos or teammates.

---

## 7. Testing & Validation

```bash
pip install -r requirements.txt
python -m pytest
```

The included tests cover synthetic-data generation and text sanitization. Extend them with API contract tests or DB assertions as you iterate.

---

## 8. What to Present as “Output”

- **Data artifacts:** `data/raw_*.csv`, `data/processed/*.csv`, `data/support_analytics.db`.
- **API responses:** JSON payloads from `/api/tickets/*` and `/api/telemetry/events`.
- **Dashboards:** Power BI visuals saved as PNGs/GIFs for recruiters.
- **Logs:** ETL + API logs (via `loguru`) for observability stories.

Use this README alongside the main project documentation when presenting the project in your portfolio or during technical interviews.

