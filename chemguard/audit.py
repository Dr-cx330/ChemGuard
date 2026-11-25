import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

DB_PATH = Path(os.environ.get("CHEMGUARD_DB", "chemguard_audit.sqlite3"))


def record(operation: dict, decision: str, reasons: list[str]) -> str:
    event_id = str(uuid4())
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as db:
        db.execute("CREATE TABLE IF NOT EXISTS audit (id TEXT PRIMARY KEY, created_at TEXT, operation TEXT, decision TEXT, reasons TEXT)")
        db.execute("INSERT INTO audit VALUES (?, ?, ?, ?, ?)", (event_id, datetime.now(timezone.utc).isoformat(), json.dumps(operation, ensure_ascii=False), decision, json.dumps(reasons, ensure_ascii=False)))
    return event_id
