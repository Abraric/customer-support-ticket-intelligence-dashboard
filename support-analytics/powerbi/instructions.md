# Power BI Dashboard Instructions

## 1. Connect to the SQLite Database
1. Open **Power BI Desktop** → *Get Data* → *More...*.
2. Choose **Database → SQLite** (install the official SQLite connector if prompted).
3. Browse to `support-analytics/data/support_analytics.db`.
4. Select tables: `tickets`, `ticket_nlp`, `telemetry`, `ticket_summary`.
5. Establish relationships:
   - `tickets.ticket_id` ↔ `ticket_nlp.ticket_id`.
   - `ticket_summary.category` ↔ `ticket_nlp.predicted_category`.

> For PostgreSQL deployments, replace the connector selection with *PostgreSQL* and supply the connection string from `.env`.

## 2. Connect to FastAPI Endpoints
1. *Get Data* → **Web**.
2. Use endpoints (ensure `uvicorn api.main:app --reload` is running):
   - `http://localhost:8000/api/tickets/top-categories`
   - `http://localhost:8000/api/tickets/sentiment-summary`
   - `http://localhost:8000/api/tickets/trends`
   - `http://localhost:8000/api/telemetry/events?limit=500`
3. Convert the JSON responses to tables using *Transform Data*.
4. Schedule refreshes via **Power BI Gateway** for on-prem data or host the API for cloud dashboards.

## 3. Recommended Visuals
- **Ticket Volume Trends**: Line chart using `tickets.trend_date` (or API dataset) vs. `ticket_count`.
- **Category Breakdown Pie**: Pie chart with `ticket_summary.category`.
- **Sentiment Score Cards**: Three KPI cards using the sentiment summary dataset.
- **Issue Heatmap**: Matrix by `tickets.product` and `tickets.severity` counting tickets.
- **Telemetry Spike Detection**: Area chart from `telemetry` filtering `event_type IN ('IOPS Spike','CPU Spike')`.
- **AI Summary Card**: Multi-row card highlighting key metrics (e.g., top category, avg resolution).

## 4. DAX Snippets
```DAX
Avg Resolution Hours =
AVERAGE ( tickets[resolution_hours] )

Sentiment Ratio =
DIVIDE (
    CALCULATE ( COUNT ( ticket_nlp[ticket_id] ), ticket_nlp[sentiment_label] = "Positive" ),
    CALCULATE ( COUNT ( ticket_nlp[ticket_id] ) )
)

MoM Ticket Growth % =
VAR CurrentMonth =
    CALCULATE ( COUNT ( tickets[ticket_id] ), SAMEPERIODLASTYEAR ( 'Date'[Date] ) )
VAR PreviousMonth =
    CALCULATE ( COUNT ( tickets[ticket_id] ), DATEADD ( 'Date'[Date], -1, MONTH ) )
RETURN
    DIVIDE ( CurrentMonth - PreviousMonth, PreviousMonth )
```

## 5. Publishing Tips
- Use parameters for API base URLs (`prod`, `staging`).
- Enable incremental refresh for telemetry tables due to volume.
- Layer alert rules on KPI cards for SLA breaches (e.g., avg resolution > 48h).

## 6. Screenshot Placeholders
- `images/ticket_volume.png` – Trend line.
- `images/category_breakdown.png` – Pie Chart.
- `images/sentiment_cards.png` – KPI tiles.
- `images/telemetry_heatmap.png` – Heatmap for node events.

