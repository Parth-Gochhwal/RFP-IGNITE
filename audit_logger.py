from datetime import datetime
import json
from pathlib import Path
from typing import Any


def _audit_file_path() -> Path:
    # place audit file under repo_root/data/audit_log.json
    repo_root = Path(__file__).resolve().parent
    data_dir = repo_root / "data"
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        # best-effort; if we can't create, fallback to relative path
        pass
    return data_dir / "audit_log.json"


def log_event(event_type: str, payload: dict, pipeline_run_id: str | None = None) -> bool:
    """Append an event to the audit log (safe, non-raising).

    Returns True on success, False on failure.
    Each event: timestamp (UTC ISO), event_type, payload
    """
    try:
        file_path = _audit_file_path()
        event = {
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "pipeline_run_id": pipeline_run_id,
            "event_type": event_type,
            "payload": payload,
        }

        existing = []
        if file_path.exists():
            try:
                existing = json.loads(file_path.read_text(encoding='utf-8') or "[]")
                if not isinstance(existing, list):
                    existing = []
            except Exception:
                existing = []

        existing.append(event)
        try:
            file_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding='utf-8')
            return True
        except Exception:
            return False
    except Exception:
        return False
