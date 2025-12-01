from __future__ import annotations

from datetime import datetime, date
from typing import List, Optional

from pydantic import BaseModel


class TicketCategoryResponse(BaseModel):
    category: str
    ticket_count: int
    avg_resolution_hours: float


class TicketSentimentSummary(BaseModel):
    positive_percent: float
    negative_percent: float
    neutral_percent: float


class TicketTrendPoint(BaseModel):
    date: date
    ticket_count: int


class TelemetryEventResponse(BaseModel):
    event_id: str
    node_id: str
    product: str
    event_type: str
    response_time_ms: int
    cpu_usage: float
    storage_utilization: float
    health_severity: str
    response_time_bucket: str
    created_at: datetime


class TelemetryFilter(BaseModel):
    product: Optional[str] = None
    severity: Optional[str] = None
    timeframe_days: Optional[int] = None


TicketCategoryList = List[TicketCategoryResponse]
TelemetryResponseList = List[TelemetryEventResponse]

