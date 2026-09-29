"""Print concise PostgreSQL and Redis runtime evidence."""

import os

from redis import Redis
from sqlalchemy import create_engine, text


redis = Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
print("redis_version", redis.info()["redis_version"])
print("stream_length", redis.xlen("honeypot:jobs"))
print("stream_groups", redis.xinfo_groups("honeypot:jobs"))

queries = {
    "postgres_version": "select version()",
    "alembic": "select version_num from alembic_version",
    "tables": "select count(*) from pg_tables where schemaname='public'",
    "indexes": "select count(*) from pg_indexes where schemaname='public'",
    "events": "select count(*) from events",
    "detections": "select count(*) from detections",
    "incidents": "select count(*) from incidents",
    "alerts": "select count(*) from alerts",
    "audit_logs": "select count(*) from audit_logs",
    "refresh_tokens": "select count(*) from refresh_tokens",
    "password_reset_tokens": "select count(*) from password_reset_tokens",
    "predictions": "select count(*) from ml_predictions",
    "threat_intelligence": "select count(*) from threat_intel",
}
with create_engine(os.environ["DATABASE_URL"]).connect() as connection:
    for label, query in queries.items():
        print(label, connection.execute(text(query)).scalar())
