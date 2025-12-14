"""
Simple file-based store for saving review drafts and approved reviews.
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from review.models import ApprovedReview, ReviewDraft


class ReviewStore:
    """File-based store for review drafts and approved reviews."""

    def __init__(self, base_path: Optional[Path] = None):
        if base_path is None:
            project_root = Path(__file__).resolve().parent.parent
            base_path = project_root / "data" / "reviews"
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_draft_path(self, rfp_id: str) -> Path:
        """Get path for draft file."""
        return self.base_path / f"{rfp_id}_draft.json"

    def _get_approved_path(self, rfp_id: str) -> Path:
        """Get path for approved file."""
        return self.base_path / f"{rfp_id}_approved.json"

    def _atomic_write(self, path: Path, data: Dict) -> None:
        """Write JSON file atomically (write to temp then rename)."""
        # Write to temp file in same directory
        temp_path = path.with_suffix(".tmp")
        with temp_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        # Atomic rename
        temp_path.replace(path)

    def save_draft(self, rfp_id: str, draft: ReviewDraft) -> None:
        """Save a review draft."""
        path = self._get_draft_path(rfp_id)
        self._atomic_write(path, draft.to_dict())

    def load_draft(self, rfp_id: str) -> Optional[ReviewDraft]:
        """Load the latest draft for an RFP, if it exists."""
        path = self._get_draft_path(rfp_id)
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return ReviewDraft.from_dict(data)

    def save_approved(self, rfp_id: str, approved: ApprovedReview) -> None:
        """Save an approved review."""
        path = self._get_approved_path(rfp_id)
        self._atomic_write(path, approved.to_dict())

    def load_approved(self, rfp_id: str) -> Optional[ApprovedReview]:
        """Load the approved review for an RFP, if it exists."""
        path = self._get_approved_path(rfp_id)
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return ApprovedReview.from_dict(data)

    def list_reviews(self) -> Dict[str, Dict[str, Optional[datetime]]]:
        """
        List all RFPs with review status.
        Returns dict mapping rfp_id to {draft_at, approved_at}.
        """
        result: Dict[str, Dict[str, Optional[datetime]]] = {}
        
        # Scan for draft files
        for path in self.base_path.glob("*_draft.json"):
            rfp_id = path.stem.replace("_draft", "")
            if rfp_id not in result:
                result[rfp_id] = {"draft_at": None, "approved_at": None}
            try:
                draft = self.load_draft(rfp_id)
                if draft:
                    result[rfp_id]["draft_at"] = draft.saved_at
            except Exception:
                pass

        # Scan for approved files
        for path in self.base_path.glob("*_approved.json"):
            rfp_id = path.stem.replace("_approved", "")
            if rfp_id not in result:
                result[rfp_id] = {"draft_at": None, "approved_at": None}
            try:
                approved = self.load_approved(rfp_id)
                if approved:
                    result[rfp_id]["approved_at"] = approved.approved_at
            except Exception:
                pass

        return result

