"""NLP utilities for ticket classification and sentiment analysis."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

import spacy
from loguru import logger

try:
    from transformers import pipeline
except Exception:  # pragma: no cover - transformers optional at runtime
    pipeline = None  # type: ignore


CATEGORY_RULES: Dict[str, Iterable[str]] = {
    "Backup Failure": ["backup", "restore", "snapshot", "archive", "replication"],
    "Performance Issue": [
        "latency",
        "throughput",
        "performance",
        "slow",
        "throttle",
        "iops",
    ],
    "Access/Authentication": [
        "token",
        "login",
        "authentication",
        "ldap",
        "sso",
        "access",
        "permission",
    ],
    "Storage Capacity": [
        "capacity",
        "storage",
        "utilization",
        "disk",
        "space",
        "tier",
    ],
    "Security/Threat": ["ransomware", "threat", "anomaly", "security", "alert"],
    "Other": [],
}


SENTIMENT_DEFAULT_THRESHOLD = 0.55


@dataclass
class SentimentResult:
    label: str
    score: float


class TicketNLPProcessor:
    """Wrap spaCy category heuristics + HuggingFace sentiment pipeline."""

    def __init__(self, sentiment_model: str) -> None:
        self._nlp = spacy.blank("en")
        self._sentiment_model_name = sentiment_model
        self._sentiment_pipeline = self._load_sentiment_pipeline(sentiment_model)
        logger.info("TicketNLPProcessor initialized with %s", sentiment_model)

    def _load_sentiment_pipeline(self, model_name: str):
        if pipeline is None:
            logger.warning("transformers pipeline unavailable; using heuristics only")
            return None
        try:
            return pipeline("sentiment-analysis", model=model_name)
        except Exception as exc:  # pragma: no cover - transformers download failure
            logger.warning("Falling back to heuristic sentiment: %s", exc)
            return None

    def predict_category(self, text: str) -> str:
        text_lower = text.lower()
        for category, keywords in CATEGORY_RULES.items():
            if category == "Other":
                continue
            if any(keyword in text_lower for keyword in keywords):
                return category
        return "Other"

    def analyze_sentiment(self, text: str) -> SentimentResult:
        if not text.strip():
            return SentimentResult("neutral", 0.0)
        if self._sentiment_pipeline:
            try:
                result = self._sentiment_pipeline(text[:512])[0]
                label = result["label"].lower()
                score = float(result["score"])
                if "neg" in label:
                    label = "negative"
                elif "pos" in label:
                    label = "positive"
                else:
                    label = "neutral"
                return SentimentResult(label, score)
            except Exception as exc:  # pragma: no cover - runtime fallback
                logger.warning("Sentiment pipeline error, using heuristic: %s", exc)
        return self._heuristic_sentiment(text)

    def _heuristic_sentiment(self, text: str) -> SentimentResult:
        text_lower = text.lower()
        negative_triggers = ["failure", "offline", "error", "alert", "issue", "threat"]
        positive_triggers = ["resolved", "success", "restored"]
        score = 0.5
        label = "neutral"
        if any(tok in text_lower for tok in negative_triggers):
            score = 0.2
            label = "negative"
        elif any(tok in text_lower for tok in positive_triggers):
            score = 0.8
            label = "positive"
        return SentimentResult(label, score)


def sanitize_text(value: str) -> str:
    """Normalize whitespace to keep downstream processing clean."""
    return re.sub(r"\\s+", " ", value).strip()


