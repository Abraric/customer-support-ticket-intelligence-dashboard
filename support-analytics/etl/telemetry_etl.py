"""Telemetry ETL pipeline for Cohesity-style node metrics."""

from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta
from typing import List

import numpy as np
import pandas as pd
from loguru import logger

from config import get_settings
from database.init_db import create_schema, load_telemetry

PRODUCTS = [
    "Cohesity DataProtect",
    "Cohesity SmartFiles",
    "Cohesity FortKnox",
    "Cohesity SiteContinuity",
]

EVENT_TYPES = [
    "IOPS Spike",
    "CPU Spike",
    "Node Offline",
    "Snapshot Success",
    "Snapshot Failure",
    "Security Alert",
    "Network Congestion",
    "Disk Rebuild",
    "Throughput Drop",
    "Upgrade Event",
]


def synthesize_telemetry_rows(record_count: int, seed: int = 7) -> pd.DataFrame:
    random.seed(seed)
    np.random.seed(seed)
    settings = get_settings()
    start = datetime.utcnow() - timedelta(days=120)
    rows: List[dict] = []
    for _ in range(record_count):
        created = start + timedelta(minutes=random.randint(0, 120 * 24 * 60))
        node_id = f"NODE-{random.randint(1, 300)}"
        rows.append(
            {
                "event_id": f"EVT-{random.randint(10_000, 99_999)}-{random.randint(0, 999)}",
                "node_id": node_id,
                "event_type": random.choice(EVENT_TYPES),
                "response_time_ms": max(5, int(np.random.normal(45, 20))),
                "cpu_usage": round(min(100, max(1, np.random.normal(55, 18))), 2),
                "storage_utilization": round(
                    min(100, max(5, np.random.normal(68, 12))), 2
                ),
                "created_at": created.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    df = pd.DataFrame(rows)
    settings.telemetry_raw_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(settings.telemetry_raw_path, index=False)
    logger.success(
        "Generated %s synthetic telemetry events at %s",
        len(df),
        settings.telemetry_raw_path,
    )
    return df


def classify_health(row) -> str:
    if row["event_type"] in {"Security Alert", "Node Offline", "Snapshot Failure"}:
        return "Critical"
    if row["cpu_usage"] > 85 or row["storage_utilization"] > 90:
        return "High"
    if row["response_time_ms"] > 80:
        return "Elevated"
    return "Normal"


def assign_product(node_id: str) -> str:
    index = abs(hash(node_id)) % len(PRODUCTS)
    return PRODUCTS[index]


def enrich_telemetry(df: pd.DataFrame) -> pd.DataFrame:
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["health_severity"] = df.apply(classify_health, axis=1)
    df["product"] = df["node_id"].apply(assign_product)
    df["response_time_bucket"] = pd.cut(
        df["response_time_ms"],
        bins=[0, 25, 50, 75, 100, 999],
        labels=["<25ms", "25-50ms", "50-75ms", "75-100ms", "100ms+"],
        include_lowest=True,
    )
    return df


def persist_processed(df: pd.DataFrame, file_name: str = "telemetry_processed.csv") -> str:
    settings = get_settings()
    output_path = settings.processed_dir / file_name
    df.to_csv(output_path, index=False)
    logger.success("Saved processed telemetry to %s", output_path)
    return str(output_path)


def run_telemetry_pipeline(
    generate_if_missing: bool = True,
    record_count: int = 7500,
) -> pd.DataFrame:
    settings = get_settings()
    if not settings.telemetry_raw_path.exists() and generate_if_missing:
        synthesize_telemetry_rows(record_count=record_count)
    df = pd.read_csv(settings.telemetry_raw_path)
    df = enrich_telemetry(df)
    persist_processed(df)
    create_schema()
    load_telemetry(df)
    return df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Telemetry ETL runner")
    parser.add_argument(
        "--generate-raw",
        action="store_true",
        help="Force regenerate of telemetry CSV before processing",
    )
    parser.add_argument(
        "--records",
        type=int,
        default=7500,
        help="Number of synthetic events to generate",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.generate_raw:
        synthesize_telemetry_rows(record_count=args.records)
    run_telemetry_pipeline(generate_if_missing=True, record_count=args.records)
"""Telemetry ETL pipeline for Cohesity-style node metrics."""

from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta
from typing import List

import numpy as np
import pandas as pd
from loguru import logger

from config import get_settings

PRODUCTS = [
    "Cohesity DataProtect",
    "Cohesity SmartFiles",
    "Cohesity FortKnox",
    "Cohesity SiteContinuity",
]

EVENT_TYPES = [
    "IOPS Spike",
    "CPU Spike",
    "Node Offline",
    "Snapshot Success",
    "Snapshot Failure",
    "Security Alert",
    "Network Congestion",
    "Disk Rebuild",
    "Throughput Drop",
    "Upgrade Event",
]


def synthesize_telemetry_rows(record_count: int, seed: int = 7) -> pd.DataFrame:
    random.seed(seed)
    np.random.seed(seed)
    settings = get_settings()
    start = datetime.utcnow() - timedelta(days=120)
    rows: List[dict] = []
    for _ in range(record_count):
        created = start + timedelta(minutes=random.randint(0, 120 * 24 * 60))
        node_id = f"NODE-{random.randint(1, 300)}"
        rows.append(
            {
                "event_id": f"EVT-{random.randint(10_000, 99_999)}-{random.randint(0, 999)}",
                "node_id": node_id,
                "event_type": random.choice(EVENT_TYPES),
                "response_time_ms": max(5, int(np.random.normal(45, 20))),
                "cpu_usage": round(min(100, max(1, np.random.normal(55, 18))), 2),
                "storage_utilization": round(
                    min(100, max(5, np.random.normal(68, 12))), 2
                ),
                "created_at": created.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    df = pd.DataFrame(rows)
    settings.telemetry_raw_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(settings.telemetry_raw_path, index=False)
    logger.success(
        "Generated %s synthetic telemetry events at %s",
        len(df),
        settings.telemetry_raw_path,
    )
    return df


def classify_health(row) -> str:
    if row["event_type"] in {"Security Alert", "Node Offline", "Snapshot Failure"}:
        return "Critical"
    if row["cpu_usage"] > 85 or row["storage_utilization"] > 90:
        return "High"
    if row["response_time_ms"] > 80:
        return "Elevated"
    return "Normal"


def assign_product(node_id: str) -> str:
    index = (abs(hash(node_id)) % len(PRODUCTS))
    return PRODUCTS[index]


def enrich_telemetry(df: pd.DataFrame) -> pd.DataFrame:
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["health_severity"] = df.apply(classify_health, axis=1)
    df["product"] = df["node_id"].apply(assign_product)
    df["response_time_bucket"] = pd.cut(
        df["response_time_ms"],
        bins=[0, 25, 50, 75, 100, 999],
        labels=["<25ms", "25-50ms", "50-75ms", "75-100ms", "100ms+"],
        include_lowest=True,
    )
    return df


def persist_processed(df: pd.DataFrame, file_name: str = "telemetry_processed.csv") -> str:
    settings = get_settings()
    output_path = settings.processed_dir / file_name
    df.to_csv(output_path, index=False)
    logger.success("Saved processed telemetry to %s", output_path)
    return str(output_path)


def run_telemetry_pipeline(
    generate_if_missing: bool = True,
    record_count: int = 7500,
) -> pd.DataFrame:
    settings = get_settings()
    if not settings.telemetry_raw_path.exists() and generate_if_missing:
        synthesize_telemetry_rows(record_count=record_count)
    df = pd.read_csv(settings.telemetry_raw_path)
    df = enrich_telemetry(df)
    persist_processed(df)
    return df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Telemetry ETL runner")
    parser.add_argument(
        "--generate-raw",
        action="store_true",
        help="Force regenerate of telemetry CSV before processing",
    )
    parser.add_argument(
        "--records",
        type=int,
        default=7500,
        help="Number of synthetic events to generate",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.generate_raw:
        synthesize_telemetry_rows(record_count=args.records)
    run_telemetry_pipeline(generate_if_missing=True, record_count=args.records)

