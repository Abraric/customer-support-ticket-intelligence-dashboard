from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from loguru import logger

from config import get_settings
from database import models
from database.session import SessionLocal, Base, engine


def create_schema() -> None:
    logger.info("Creating database schema if missing")
    Base.metadata.create_all(bind=engine)


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Expected processed file missing: {path}")
    return pd.read_csv(path)


def load_tickets(df: pd.DataFrame) -> None:
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["resolved_at"] = pd.to_datetime(df["resolved_at"], errors="coerce")
    with SessionLocal() as session:
        for record in df.to_dict(orient="records"):
            ticket = models.Ticket(
                ticket_id=record["ticket_id"],
                customer_id=record["customer_id"],
                product=record["product"],
                issue_description=record["issue_description"],
                severity=record["severity"],
                status=record["status"],
                created_at=record["created_at"],
                resolved_at=record["resolved_at"],
                resolution_hours=record["resolution_hours"],
                severity_score=record["severity_score"],
            )
            nlp = models.TicketNLP(
                ticket_id=record["ticket_id"],
                predicted_category=record["predicted_category"],
                sentiment_label=record["sentiment_label"],
                sentiment_score=record["sentiment_score"],
            )
            session.merge(ticket)
            session.merge(nlp)
        session.commit()
        logger.success("Loaded %s ticket rows into DB", len(df))


def load_telemetry(df: pd.DataFrame) -> None:
    df["created_at"] = pd.to_datetime(df["created_at"])
    with SessionLocal() as session:
        for record in df.to_dict(orient="records"):
            telemetry = models.TelemetryEvent(
                event_id=record["event_id"],
                node_id=record["node_id"],
                product=record["product"],
                event_type=record["event_type"],
                response_time_ms=record["response_time_ms"],
                cpu_usage=record["cpu_usage"],
                storage_utilization=record["storage_utilization"],
                health_severity=record["health_severity"],
                response_time_bucket=record["response_time_bucket"],
                created_at=record["created_at"],
            )
            session.merge(telemetry)
        session.commit()
        logger.success("Loaded %s telemetry rows into DB", len(df))


def refresh_summary() -> None:
    with SessionLocal() as session:
        session.query(models.TicketSummary).delete()
        session.commit()
        stmt = """
            SELECT tnl.predicted_category AS category,
                   COUNT(*) AS ticket_count,
                   AVG(t.resolution_hours) AS avg_resolution_hours,
                   SUM(CASE WHEN tnl.sentiment_label = 'positive' THEN 1 ELSE 0 END)*1.0/COUNT(*) AS positive_percent,
                   SUM(CASE WHEN tnl.sentiment_label = 'negative' THEN 1 ELSE 0 END)*1.0/COUNT(*) AS negative_percent,
                   SUM(CASE WHEN tnl.sentiment_label = 'neutral' THEN 1 ELSE 0 END)*1.0/COUNT(*) AS neutral_percent
            FROM tickets t
            JOIN ticket_nlp tnl ON t.ticket_id = tnl.ticket_id
            GROUP BY tnl.predicted_category
        """
        result = session.execute(stmt)
        for row in result:
            summary = models.TicketSummary(
                category=row.category,
                ticket_count=row.ticket_count,
                avg_resolution_hours=row.avg_resolution_hours or 0,
                positive_percent=row.positive_percent or 0,
                negative_percent=row.negative_percent or 0,
                neutral_percent=row.neutral_percent or 0,
            )
            session.add(summary)
        session.commit()
        logger.success("Refreshed ticket_summary table")


def initialize_database(tickets_file: str = "tickets_processed.csv", telemetry_file: str = "telemetry_processed.csv") -> None:
    settings = get_settings()
    create_schema()
    ticket_df = load_csv(settings.processed_dir / tickets_file)
    telemetry_df = load_csv(settings.processed_dir / telemetry_file)
    load_tickets(ticket_df)
    load_telemetry(telemetry_df)
    refresh_summary()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize analytics database")
    parser.add_argument(
        "--tickets",
        type=str,
        default="tickets_processed.csv",
        help="Processed tickets file name relative to processed directory",
    )
    parser.add_argument(
        "--telemetry",
        type=str,
        default="telemetry_processed.csv",
        help="Processed telemetry file name relative to processed directory",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    initialize_database(tickets_file=args.tickets, telemetry_file=args.telemetry)

