"""Ticket ETL pipeline orchestrating data generation, cleansing, and NLP enrichment."""

from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta
from typing import List

import numpy as np
import pandas as pd
from loguru import logger

from config import get_settings
from database.init_db import create_schema, load_tickets, refresh_summary
from etl.nlp_model import TicketNLPProcessor, sanitize_text

SEVERITY_SCORE = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}


def synthesize_ticket_rows(record_count: int, seed: int = 42) -> pd.DataFrame:
    """Create a synthetic ticket dataset resembling Cohesity workloads."""
    random.seed(seed)
    np.random.seed(seed)
    settings = get_settings()
    products = [
        "Cohesity DataProtect",
        "Cohesity SmartFiles",
        "Cohesity FortKnox",
        "Cohesity SiteContinuity",
    ]
    issue_types = [
        "Backup job failure due to snapshot metadata corruption",
        "Deduplication ratio drop impacting cluster capacity",
        "Replication lag between data centers",
        "Ransomware anomaly detected via ML sensor",
        "Restore throughput throttled below SLA",
        "API token invalidation impacting automation",
        "Node offline after firmware upgrade",
        "Audit log ingestion halted",
        "Storage domain marked read-only",
        "S3 compatible endpoint intermittent",
    ]
    severities = ["Low", "Medium", "High", "Critical"]
    statuses = ["Open", "In Progress", "Resolved", "Escalated"]
    start = datetime.utcnow() - timedelta(days=120)
    rows: List[dict] = []
    for idx in range(record_count):
        created = start + timedelta(minutes=random.randint(0, 120 * 24 * 60))
        resolved = (
            created + timedelta(hours=random.randint(4, 240))
            if random.random() > 0.2
            else None
        )
        rows.append(
            {
                "ticket_id": f"TKT-{12000+idx}",
                "customer_id": f"CUST-{random.randint(100, 999)}",
                "product": random.choice(products),
                "issue_description": random.choice(issue_types),
                "severity": random.choices(severities, weights=[0.2, 0.45, 0.25, 0.1])[0],
                "status": random.choice(statuses),
                "created_at": created.strftime("%Y-%m-%d %H:%M:%S"),
                "resolved_at": resolved.strftime("%Y-%m-%d %H:%M:%S") if resolved else "",
            }
        )
    df = pd.DataFrame(rows)
    settings.ticket_raw_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(settings.ticket_raw_path, index=False)
    logger.success(
        "Generated %s synthetic tickets at %s",
        len(df),
        settings.ticket_raw_path,
    )
    return df


def load_ticket_csv(path) -> pd.DataFrame:
    logger.info("Loading tickets from %s", path)
    return pd.read_csv(path)


def enrich_with_features(df: pd.DataFrame, nlp: TicketNLPProcessor) -> pd.DataFrame:
    df["issue_description"] = df["issue_description"].astype(str).apply(sanitize_text)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["resolved_at"] = pd.to_datetime(df["resolved_at"], errors="coerce")
    df["resolution_hours"] = (
        (df["resolved_at"] - df["created_at"]).dt.total_seconds() / 3600
    ).fillna(0)
    df["severity_score"] = df["severity"].map(SEVERITY_SCORE).fillna(1)
    df["predicted_category"] = df["issue_description"].apply(nlp.predict_category)
    sentiments = df["issue_description"].apply(nlp.analyze_sentiment)
    df["sentiment_label"] = sentiments.apply(lambda s: s.label)
    df["sentiment_score"] = sentiments.apply(lambda s: round(s.score, 4))
    return df


def persist_processed(df: pd.DataFrame, file_name: str = "tickets_processed.csv") -> str:
    settings = get_settings()
    output_path = settings.processed_dir / file_name
    df.to_csv(output_path, index=False)
    logger.success("Saved processed tickets to %s", output_path)
    return str(output_path)


def run_ticket_pipeline(
    generate_if_missing: bool = True,
    record_count: int = 1500,
) -> pd.DataFrame:
    """Full pipeline orchestrator used by CLI/tests."""
    settings = get_settings()
    nlp = TicketNLPProcessor(settings.huggingface_model)

    if not settings.ticket_raw_path.exists() and generate_if_missing:
        logger.warning(
            "ticket file missing at %s. Generating %s rows.",
            settings.ticket_raw_path,
            record_count,
        )
        synthesize_ticket_rows(record_count=record_count)

    df = load_ticket_csv(settings.ticket_raw_path)
    df = enrich_with_features(df, nlp)
    persist_processed(df)
    create_schema()
    load_tickets(df)
    refresh_summary()
    return df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ticket ETL runner")
    parser.add_argument(
        "--generate-raw",
        action="store_true",
        help="Force regeneration of the raw CSV before processing",
    )
    parser.add_argument(
        "--records",
        type=int,
        default=1500,
        help="Number of synthetic tickets to generate when bootstrapping",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.generate_raw:
        synthesize_ticket_rows(record_count=args.records)
    run_ticket_pipeline(generate_if_missing=True, record_count=args.records)


