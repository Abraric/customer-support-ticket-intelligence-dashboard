from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from database.session import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String, unique=True, index=True, nullable=False)
    customer_id = Column(String, nullable=False)
    product = Column(String, nullable=False)
    issue_description = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolution_hours = Column(Float, nullable=False, default=0.0)
    severity_score = Column(Integer, nullable=False, default=1)

    nlp = relationship("TicketNLP", back_populates="ticket", uselist=False, cascade="all,delete")


class TicketNLP(Base):
    __tablename__ = "ticket_nlp"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String, ForeignKey("tickets.ticket_id"), nullable=False, unique=True)
    predicted_category = Column(String, nullable=False)
    sentiment_label = Column(String, nullable=False)
    sentiment_score = Column(Float, nullable=False)

    ticket = relationship("Ticket", back_populates="nlp")


class TelemetryEvent(Base):
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, nullable=False)
    node_id = Column(String, nullable=False)
    product = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    response_time_ms = Column(Integer, nullable=False)
    cpu_usage = Column(Float, nullable=False)
    storage_utilization = Column(Float, nullable=False)
    health_severity = Column(String, nullable=False)
    response_time_bucket = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)


class TicketSummary(Base):
    __tablename__ = "ticket_summary"
    __table_args__ = (
        UniqueConstraint("category", name="uq_ticket_summary_category"),
    )

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False)
    ticket_count = Column(Integer, nullable=False)
    avg_resolution_hours = Column(Float, nullable=False)
    positive_percent = Column(Float, nullable=False)
    negative_percent = Column(Float, nullable=False)
    neutral_percent = Column(Float, nullable=False)

