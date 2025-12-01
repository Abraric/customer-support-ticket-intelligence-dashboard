CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id TEXT UNIQUE,
    customer_id TEXT,
    product TEXT,
    issue_description TEXT,
    severity TEXT,
    status TEXT,
    created_at TEXT,
    resolved_at TEXT,
    resolution_hours REAL,
    severity_score INTEGER
);

CREATE TABLE IF NOT EXISTS ticket_nlp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id TEXT REFERENCES tickets(ticket_id),
    predicted_category TEXT,
    sentiment_label TEXT,
    sentiment_score REAL
);

CREATE TABLE IF NOT EXISTS telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE,
    node_id TEXT,
    product TEXT,
    event_type TEXT,
    response_time_ms INTEGER,
    cpu_usage REAL,
    storage_utilization REAL,
    health_severity TEXT,
    response_time_bucket TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS ticket_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    ticket_count INTEGER,
    avg_resolution_hours REAL,
    positive_percent REAL,
    negative_percent REAL,
    neutral_percent REAL
);

