from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from api import schemas
from config import get_settings
from database.models import TelemetryEvent, Ticket, TicketNLP
from database.session import get_session


router = APIRouter(prefix="/api", tags=["Analytics"])


@router.get(
    "/tickets/top-categories",
    response_model=List[schemas.TicketCategoryResponse],
)
def get_top_categories(session: Session = Depends(get_session)):
    stmt = (
        select(
            TicketNLP.predicted_category.label("category"),
            func.count(Ticket.ticket_id).label("ticket_count"),
            func.avg(Ticket.resolution_hours).label("avg_resolution_hours"),
        )
        .join(TicketNLP, Ticket.ticket_id == TicketNLP.ticket_id)
        .group_by(TicketNLP.predicted_category)
        .order_by(func.count(Ticket.ticket_id).desc())
    )
    rows = session.execute(stmt).all()
    return [
        schemas.TicketCategoryResponse(
            category=row.category,
            ticket_count=row.ticket_count,
            avg_resolution_hours=round(row.avg_resolution_hours or 0, 2),
        )
        for row in rows
    ]


@router.get(
    "/tickets/sentiment-summary",
    response_model=schemas.TicketSentimentSummary,
)
def sentiment_summary(session: Session = Depends(get_session)):
    stmt = select(
        func.count().label("total"),
        func.sum(case((TicketNLP.sentiment_label == "positive", 1), else_=0)).label(
            "positive"
        ),
        func.sum(case((TicketNLP.sentiment_label == "negative", 1), else_=0)).label(
            "negative"
        ),
        func.sum(case((TicketNLP.sentiment_label == "neutral", 1), else_=0)).label(
            "neutral"
        ),
    )
    row = session.execute(stmt).one()
    total = row.total or 1
    return schemas.TicketSentimentSummary(
        positive_percent=round((row.positive or 0) / total * 100, 2),
        negative_percent=round((row.negative or 0) / total * 100, 2),
        neutral_percent=round((row.neutral or 0) / total * 100, 2),
    )


@router.get(
    "/tickets/trends",
    response_model=List[schemas.TicketTrendPoint],
)
def ticket_trends(session: Session = Depends(get_session)):
    settings = get_settings()
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=settings.trend_window_days)
    stmt = (
        select(
            func.date(Ticket.created_at).label("day"),
            func.count(Ticket.ticket_id).label("ticket_count"),
        )
        .where(Ticket.created_at >= start_date)
        .group_by(func.date(Ticket.created_at))
        .order_by(func.date(Ticket.created_at))
    )
    rows = session.execute(stmt).all()
    return [
        schemas.TicketTrendPoint(date=row.day, ticket_count=row.ticket_count)
        for row in rows
    ]


@router.get(
    "/telemetry/events",
    response_model=List[schemas.TelemetryEventResponse],
)
def telemetry_events(
    product: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None, description="health severity filter"),
    timeframe: Optional[int] = Query(
        default=None, description="limit to last N days of events"
    ),
    limit: int = Query(default=200, ge=1, le=1000),
    session: Session = Depends(get_session),
):
    stmt = select(TelemetryEvent).order_by(TelemetryEvent.created_at.desc()).limit(limit)
    if product:
        stmt = stmt.where(TelemetryEvent.product == product)
    if severity:
        stmt = stmt.where(TelemetryEvent.health_severity == severity)
    if timeframe:
        window_start = datetime.utcnow() - timedelta(days=timeframe)
        stmt = stmt.where(TelemetryEvent.created_at >= window_start)
    rows = session.execute(stmt).scalars().all()
    return [
        schemas.TelemetryEventResponse(
            event_id=row.event_id,
            node_id=row.node_id,
            product=row.product,
            event_type=row.event_type,
            response_time_ms=row.response_time_ms,
            cpu_usage=row.cpu_usage,
            storage_utilization=row.storage_utilization,
            health_severity=row.health_severity,
            response_time_bucket=row.response_time_bucket,
            created_at=row.created_at,
        )
        for row in rows
    ]

